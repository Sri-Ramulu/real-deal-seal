"""Checkout. The agent can open a checkout; only the buyer can approve it; only PayPal can say it was paid.

Rules this module enforces:
- the price and the shop come from the server-side catalog, never from the caller
- one idempotency key creates at most one PayPal order
- a return from PayPal proves nothing: the order is fetched and captured server-side, and the capture
  must be COMPLETED for the exact amount before the session is marked CAPTURED
- a session can be captured once (compare-and-set), however many times the return URL is opened

Without PayPal sandbox credentials the module runs in 'simulated' mode, and says so on every response.
"""
from __future__ import annotations

import base64
import time
import uuid

import httpx

from . import config, store, warehouse

_tokens: dict[str, tuple[str, float]] = {}


class CheckoutError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def mode_for(merchant_id: str) -> str:
    return "paypal_sandbox" if config.paypal_credentials(merchant_id) else "simulated"


def _token(merchant_id: str) -> str:
    tok = _tokens.get(merchant_id)
    if tok and tok[1] > time.time() + 60:
        return tok[0]
    cid, sec = config.paypal_credentials(merchant_id)
    r = httpx.post(f"{config.PAYPAL_BASE}/v1/oauth2/token", data={"grant_type": "client_credentials"},
                   headers={"Authorization": "Basic " + base64.b64encode(f"{cid}:{sec}".encode()).decode()}, timeout=20)
    r.raise_for_status()
    j = r.json()
    _tokens[merchant_id] = (j["access_token"], time.time() + int(j.get("expires_in", 300)))
    return j["access_token"]


def _paypal(merchant_id: str, method: str, path: str, request_id: str | None = None, body: dict | None = None) -> dict:
    headers = {"Authorization": f"Bearer {_token(merchant_id)}", "Content-Type": "application/json"}
    if request_id:
        headers["PayPal-Request-Id"] = request_id
    r = httpx.request(method, f"{config.PAYPAL_BASE}{path}", headers=headers, json=body, timeout=30)
    if r.status_code >= 400:
        raise CheckoutError("paypal_error", f"PayPal answered {r.status_code}: {r.text[:300]}")
    return r.json()


def available_stock(sku: str) -> int | None:
    o = warehouse.one("SELECT stock FROM gold.agent_offers WHERE sku = ?", [sku])
    return None if o is None else max(0, o["stock"] - store.units_sold(sku))


def create(sku: str, quantity: int = 1, idempotency_key: str | None = None, actor: str = "shopper") -> dict:
    if not isinstance(quantity, int) or not 1 <= quantity <= 10:
        raise CheckoutError("bad_quantity", "Quantity must be a whole number from 1 to 10.")
    key = idempotency_key or str(uuid.uuid4())
    existing = store.session_by("idempotency_key", key)
    if existing:
        return public(existing)
    offer = warehouse.one("SELECT * FROM gold.agent_offers WHERE sku = ?", [sku])
    if not offer:
        raise CheckoutError("unknown_product", f"No product with SKU {sku}.")
    if offer["standing"] == "withdrawn":
        raise CheckoutError("seal_withdrawn", f"Real Deal Seal withdrew {offer['merchant_name']}'s seal, so checkout is turned off for this shop.")
    if not offer["paypal_checkout_available"]:
        raise CheckoutError("no_paypal_checkout", f"{offer['merchant_name']} has no PayPal connection here, so no checkout can be opened.")
    if available_stock(sku) < quantity:
        raise CheckoutError("out_of_stock", f"Only {available_stock(sku)} left of {offer['product_name']}.")
    amount = f"{float(offer['price_usd']) * quantity:.2f}"
    sid, mode, now = str(uuid.uuid4()), mode_for(offer["merchant_id"]), store.now()
    s = {"session_id": sid, "idempotency_key": key, "sku": sku, "quantity": quantity, "merchant_id": offer["merchant_id"],
         "amount_usd": amount, "mode": mode, "status": "CREATED", "paypal_order_id": None, "capture_id": None,
         "approve_url": None, "created_at": now, "updated_at": now}
    if mode == "paypal_sandbox":
        order = _paypal(offer["merchant_id"], "POST", "/v2/checkout/orders", request_id=sid, body={
            "intent": "CAPTURE",
            "purchase_units": [{"reference_id": sid, "custom_id": f"rds:{sku}:{quantity}", "description": offer["product_name"][:120],
                                "amount": {"currency_code": "USD", "value": amount}}],
            "payment_source": {"paypal": {"experience_context": {
                "brand_name": offer["merchant_name"], "user_action": "PAY_NOW", "shipping_preference": "NO_SHIPPING",
                "return_url": f"{config.PUBLIC_URL}/checkout/return", "cancel_url": f"{config.PUBLIC_URL}/checkout/cancel"}}}})
        s["paypal_order_id"] = order["id"]
        s["approve_url"] = next(l["href"] for l in order["links"] if l["rel"] in ("payer-action", "approve"))
    else:
        s["paypal_order_id"] = "SIM-" + sid[:13].upper()
        s["approve_url"] = f"{config.PUBLIC_URL}/checkout/simulated?session={sid}"
    store.insert_session(s)
    store.audit(actor, "checkout.create", sid, detail={"sku": sku, "quantity": quantity, "amount_usd": amount, "mode": mode})
    return public(s)


def complete(paypal_order_id: str) -> dict:
    """Called when the buyer comes back. Asks PayPal for the truth; never trusts the redirect."""
    s = store.session_by("paypal_order_id", paypal_order_id)
    if not s:
        raise CheckoutError("unknown_order", "This PayPal order was not opened here.")
    if s["status"] in ("CAPTURED", "CANCELLED", "FAILED"):
        return public(s)
    if not store.transition(s["session_id"], ("CREATED",), "CAPTURING"):
        return public(store.session(s["session_id"]))  # another request is already capturing
    # Stock is re-checked at the moment of capture: this session now counts as CAPTURING, so a negative balance
    # means someone else took the last unit after this checkout was opened. Nothing is captured.
    offer = warehouse.one("SELECT stock FROM gold.agent_offers WHERE sku = ?", [s["sku"]])
    if offer is None or offer["stock"] - store.units_sold(s["sku"]) < 0:
        store.transition(s["session_id"], ("CAPTURING",), "FAILED")
        store.audit("server", "checkout.capture", s["session_id"], "blocked", {"reason": "out_of_stock_at_capture"}, merchant_id=s["merchant_id"])
        raise CheckoutError("out_of_stock", "The last one sold while this checkout was open. Nothing was charged.")
    try:
        if s["mode"] == "simulated":
            capture_id, status, value, payer_ref = "SIMCAP-" + s["session_id"][:10].upper(), "COMPLETED", s["amount_usd"], s["session_id"]
        else:
            order = _paypal(s["merchant_id"], "GET", f"/v2/checkout/orders/{paypal_order_id}")
            if order["status"] == "APPROVED":
                order = _paypal(s["merchant_id"], "POST", f"/v2/checkout/orders/{paypal_order_id}/capture", request_id="cap-" + s["session_id"], body={})
            caps = [c for u in order.get("purchase_units", []) for c in u.get("payments", {}).get("captures", [])]
            if not caps:
                store.transition(s["session_id"], ("CAPTURING",), "CREATED")
                raise CheckoutError("not_approved", f"PayPal says the order is {order['status']}; the buyer has not approved it.")
            capture_id, status, value = caps[0]["id"], caps[0]["status"], caps[0]["amount"]["value"]
            payer_ref = order.get("payer", {}).get("payer_id") or s["session_id"]
        if status != "COMPLETED" or f"{float(value):.2f}" != s["amount_usd"]:
            store.transition(s["session_id"], ("CAPTURING",), "FAILED")
            store.audit("paypal", "checkout.capture", s["session_id"], "failed", {"status": status, "value": value})
            raise CheckoutError("capture_not_completed", f"PayPal capture is {status} for {value} USD; expected COMPLETED for {s['amount_usd']}.")
        store.transition(s["session_id"], ("CAPTURING",), "CAPTURED", capture_id=capture_id)
        store.audit("paypal" if s["mode"] != "simulated" else "simulator", "checkout.capture", s["session_id"], "ok", {"capture_id": capture_id}, merchant_id=s["merchant_id"])
        record_order(s, capture_id, payer_ref)
    except httpx.HTTPError as e:
        store.transition(s["session_id"], ("CAPTURING",), "CREATED")
        raise CheckoutError("paypal_unreachable", f"PayPal could not be reached: {e}") from e
    return public(store.session(s["session_id"]))


def record_order(s: dict, capture_id: str, payer_ref: str):
    """Step 10 of the shopper journey: the confirmed payment becomes an order in the business's record.
    A PayPal-confirmed capture is exported to the pipeline and refreshes the evidence. A simulated one is kept
    in the operational store for the demo but is never exported: a simulated payment is not evidence."""
    from . import onboarding, refresh
    source = "paypal_checkout" if s["mode"] == "paypal_sandbox" else "simulated_checkout"
    seq = store.one("SELECT coalesce(max(seq), 0) + 1 n FROM orders WHERE merchant_id = ?", [s["merchant_id"]])["n"]
    with store.transaction():
        store.insert("orders", {"order_id": s["paypal_order_id"], "merchant_id": s["merchant_id"], "seq": 100000 + seq, "order_date": store.today(),
                                "amount_usd": s["amount_usd"], "status": "COMPLETED", "source_system": source,
                                "payer_key": onboarding.buyer_key(s["merchant_id"], payer_ref), "item_count": s["quantity"], "capture_id": capture_id,
                                "capture_status": "COMPLETED", "invoice_id": s["session_id"], "simulated": int(source != "paypal_checkout"), "recorded_at": store.now()}, or_ignore=True)
        store.insert("payment_events", {"event_id": f"cap:{s['paypal_order_id']}", "order_id": s["paypal_order_id"], "merchant_id": s["merchant_id"],
                                        "event_type": "capture", "amount_usd": s["amount_usd"], "event_date": store.today(), "provider_ref": capture_id,
                                        "evidence_class": "paypal_sandbox_confirmed" if source == "paypal_checkout" else "simulated", "recorded_at": store.now()}, or_ignore=True)
    if source == "paypal_checkout":
        refresh.run("checkout.capture")


def record_refund(order_id: str, amount: str, provider_ref: str, source: str) -> bool:
    """Record a refund once per provider reference, then let the dependent metrics recalculate."""
    from . import refresh
    o = store.one("SELECT * FROM orders WHERE order_id = ?", [order_id])
    if not o:
        return False
    new = store.insert("payment_events", {"event_id": f"ref:{provider_ref}", "order_id": order_id, "merchant_id": o["merchant_id"], "event_type": "refund",
                                          "amount_usd": f"{float(amount):.2f}", "event_date": store.today(), "provider_ref": provider_ref,
                                          "evidence_class": "paypal_sandbox_confirmed" if o["source_system"] == "paypal_checkout" else "merchant_reported",
                                          "recorded_at": store.now()}, or_ignore=True)
    if new:
        store.audit(source, "payment.refund", order_id, merchant_id=o["merchant_id"], detail={"amount_usd": amount, "provider_ref": provider_ref})
        if o["source_system"] != "simulated_checkout":
            refresh.run("payment.refund")
    return new


def record_dispute(order_id: str, won: bool, amount: str, dispute_id: str, source: str) -> bool:
    """Record a resolved PayPal dispute once per dispute id. A dispute the seller lost counts against the record."""
    from . import refresh
    o = store.one("SELECT * FROM orders WHERE order_id = ?", [order_id])
    if not o:
        return False
    new = store.insert("payment_events", {"event_id": f"dsp:{dispute_id}", "order_id": order_id, "merchant_id": o["merchant_id"],
                                          "event_type": "dispute_won" if won else "dispute_lost", "amount_usd": f"{float(amount or 0):.2f}",
                                          "event_date": store.today(), "provider_ref": dispute_id,
                                          "evidence_class": "paypal_sandbox_confirmed" if o["source_system"] == "paypal_checkout" else "merchant_reported",
                                          "recorded_at": store.now()}, or_ignore=True)
    if new:
        store.audit(source, "payment.dispute", order_id, merchant_id=o["merchant_id"], detail={"won": won, "dispute_id": dispute_id})
        if o["source_system"] != "simulated_checkout":
            refresh.run("payment.dispute")
    return new


def refund(merchant_id: str, order_id: str) -> dict:
    """A merchant refunds one of its own orders in full. PayPal orders are refunded at PayPal first."""
    o = store.one("SELECT * FROM orders WHERE order_id = ? AND merchant_id = ?", [order_id, merchant_id])
    if not o:
        raise CheckoutError("unknown_order", "That order is not in this business's operational record.")
    if store.one("SELECT 1 FROM payment_events WHERE order_id = ? AND event_type = 'refund'", [order_id]):
        raise CheckoutError("already_refunded", "That order has already been refunded.")
    if o["source_system"] == "paypal_checkout":
        r = _paypal(merchant_id, "POST", f"/v2/payments/captures/{o['capture_id']}/refund", request_id="refund-" + order_id, body={})
        if r.get("status") not in ("COMPLETED", "PENDING"):
            raise CheckoutError("refund_failed", f"PayPal answered {r.get('status')} for the refund.")
        ref = r["id"]
    else:
        ref = "local-" + order_id
    record_refund(order_id, o["amount_usd"], ref, "owner")
    return {"refunded": True, "order_id": order_id, "amount_usd": o["amount_usd"], "provider_ref": ref}


def cancel(paypal_order_id: str) -> dict:
    s = store.session_by("paypal_order_id", paypal_order_id)
    if not s:
        raise CheckoutError("unknown_order", "This PayPal order was not opened here.")
    store.transition(s["session_id"], ("CREATED",), "CANCELLED")
    return public(store.session(s["session_id"]))


def public(s: dict) -> dict:
    offer = warehouse.one("SELECT product_name, merchant_name FROM gold.agent_offers WHERE sku = ?", [s["sku"]]) or {}
    return {"session_id": s["session_id"], "status": s["status"], "mode": s["mode"], "sku": s["sku"], "quantity": s["quantity"],
            "product_name": offer.get("product_name"), "merchant_name": offer.get("merchant_name"),
            "amount_usd": s["amount_usd"], "paypal_order_id": s["paypal_order_id"], "capture_id": s["capture_id"],
            "approve_url": s["approve_url"],
            "note": ("Simulated checkout: no PayPal sandbox credentials are configured for this shop on this server, so no PayPal call was made."
                     if s["mode"] == "simulated" else "PayPal sandbox: test money only. Only the buyer can approve; the capture is verified with PayPal server-side.")}
