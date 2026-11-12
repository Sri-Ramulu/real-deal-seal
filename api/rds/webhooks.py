"""PayPal webhooks. An event is processed only after PayPal confirms its signature, and only once.

The redirect back from PayPal is one way to learn about a capture; the webhook is the other. Both end in the same
compare-and-set, so whichever arrives second changes nothing.
"""
from __future__ import annotations

from fastapi import HTTPException

from . import checkout, config, store


def verify_with_paypal(merchant_id: str, headers: dict, event: dict) -> bool:
    """Ask PayPal whether it sent this event (POST /v1/notifications/verify-webhook-signature)."""
    webhook_id = config.paypal_webhook_id(merchant_id)
    if not webhook_id or not config.paypal_credentials(merchant_id):
        return False
    r = checkout._paypal(merchant_id, "POST", "/v1/notifications/verify-webhook-signature", body={
        "auth_algo": headers.get("paypal-auth-algo"), "cert_url": headers.get("paypal-cert-url"),
        "transmission_id": headers.get("paypal-transmission-id"), "transmission_sig": headers.get("paypal-transmission-sig"),
        "transmission_time": headers.get("paypal-transmission-time"), "webhook_id": webhook_id, "webhook_event": event})
    return r.get("verification_status") == "SUCCESS"


def _session_for(event: dict) -> dict | None:
    res = event.get("resource", {})
    order_id = res.get("supplementary_data", {}).get("related_ids", {}).get("order_id") or (res.get("id") if event.get("event_type", "").startswith("CHECKOUT.ORDER") else None)
    capture_id = next((l["href"].rstrip("/").split("/")[-1] for l in res.get("links", []) if l.get("rel") == "up" and "/captures/" in l.get("href", "")), None)
    if event.get("event_type", "").startswith("CUSTOMER.DISPUTE"):
        capture_id = next((t.get("seller_transaction_id") for t in res.get("disputed_transactions", []) if t.get("seller_transaction_id")), None)
        order_id = None
    for column, value in (("paypal_order_id", order_id), ("capture_id", capture_id or res.get("id"))):
        if value:
            s = store.session_by(column, value)
            if s:
                return s
    return None


def handle(headers: dict, event: dict) -> dict:
    event_id, kind = event.get("id"), event.get("event_type", "")
    if not event_id:
        raise HTTPException(400, "Not a PayPal webhook event.")
    s = _session_for(event)
    if not s:
        store.audit("paypal", "webhook.receive", event_id, "ignored", {"type": kind, "reason": "no matching checkout"})
        return {"processed": False, "reason": "No checkout here matches this event."}
    if not verify_with_paypal(s["merchant_id"], headers, event):
        store.audit("unknown", "webhook.receive", event_id, "denied", {"type": kind, "reason": "signature not confirmed by PayPal"}, merchant_id=s["merchant_id"])
        raise HTTPException(400, "PayPal did not confirm this event's signature. It was not processed.")
    if not store.insert("webhook_events", {"event_id": event_id, "event_type": kind, "resource_id": event.get("resource", {}).get("id"),
                                           "verified": 1, "outcome": "received", "received_at": store.now()}, or_ignore=True):
        return {"processed": False, "reason": "Duplicate delivery. Already processed."}
    outcome = "no action"
    if kind in ("CHECKOUT.ORDER.APPROVED", "PAYMENT.CAPTURE.COMPLETED"):
        outcome = checkout.complete(s["paypal_order_id"])["status"]          # asks PayPal for the order; never trusts the event body
    elif kind == "PAYMENT.CAPTURE.REFUNDED":
        res = event["resource"]
        outcome = "refund recorded" if checkout.record_refund(s["paypal_order_id"], res["amount"]["value"], res["id"], "paypal") else "refund already recorded"
    elif kind == "CUSTOMER.DISPUTE.RESOLVED":
        res = event["resource"]
        code = (res.get("dispute_outcome") or {}).get("outcome_code", "")
        if "SELLER_FAVOUR" in code or "BUYER_FAVOUR" in code:
            won = "SELLER_FAVOUR" in code
            amount = (res.get("dispute_amount") or {}).get("value", "0")
            outcome = ("dispute won" if won else "dispute lost") + (" recorded" if checkout.record_dispute(s["paypal_order_id"], won, amount, res["id"], "paypal") else ", already recorded")
        else:
            outcome = f"dispute closed without a decision ({code or 'no outcome'})"
    elif kind in ("PAYMENT.CAPTURE.DENIED", "CHECKOUT.PAYMENT-APPROVAL.REVERSED"):
        store.transition(s["session_id"], ("CREATED", "CAPTURING"), "FAILED")
        outcome = "marked failed"
    store.run("UPDATE webhook_events SET outcome = ? WHERE event_id = ?", [outcome, event_id])
    store.audit("paypal", "webhook.process", event_id, detail={"type": kind, "outcome": outcome}, merchant_id=s["merchant_id"])
    return {"processed": True, "outcome": outcome}
