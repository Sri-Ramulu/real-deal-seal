"""Onboarding a business without touching the source code: workspace, connection, catalog, records, validation.

Imports are validated row by row. Accepted rows become canonical orders and events labelled `merchant_reported`;
rejected rows come back with the reason. Nothing imported is ever treated as PayPal-confirmed.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import hmac
import io
import json
import re
import uuid

from fastapi import HTTPException

from . import auth, config, store, warehouse

BUSINESS_TYPES = ("physical", "services", "digital", "local")
FULFIL_EVENT = {"physical": "shipped", "services": "service_completed", "digital": "digital_delivered", "local": "booking_kept"}


def _slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:32] or "business"
    taken = {m["merchant_id"] for m in warehouse.rows("SELECT merchant_id FROM gold.dim_merchant")} | {m["merchant_id"] for m in store.q("SELECT merchant_id FROM merchants")}
    slug, n = base, 2
    while slug in taken:
        slug, n = f"{base}-{n}", n + 1
    return slug


def create_workspace(body: dict) -> dict:
    name = (body.get("name") or "").strip()
    if len(name) < 2:
        raise HTTPException(400, "Give the business a name.")
    if body.get("business_type") not in BUSINESS_TYPES:
        raise HTTPException(400, f"Choose a business type: {', '.join(BUSINESS_TYPES)}.")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", body.get("email") or ""):
        raise HTTPException(400, "Enter a valid email address.")
    mid = _slug(name)
    with store.transaction():
        store.insert("merchants", {"merchant_id": mid, "name": name, "business_type": body["business_type"],
                                   "category": (body.get("category") or "General").strip(), "region": (body.get("region") or "US").strip(),
                                   "sells": body.get("sells"), "ships_from": body.get("ships_from"), "returns_policy": body.get("returns_policy"),
                                   "created_at": store.now()})
        auth.create_user(mid, body["email"], body.get("password") or "", "owner")
    store.audit(body["email"], "workspace.create", mid, merchant_id=mid)
    user = store.one("SELECT * FROM merchant_users WHERE merchant_id = ?", [mid])
    return {"merchant_id": mid, "token": auth.open_session(user), "next": "Connect PayPal or import your records."}


def connect(merchant_id: str, provider: str) -> dict:
    """Record an authorised source. PayPal is 'active' only when sandbox credentials for this business are configured
    on the server and PayPal accepts them; otherwise the connection is recorded as simulated and labelled."""
    if provider == "paypal":
        if config.paypal_credentials(merchant_id):
            from . import checkout
            try:
                checkout._token(merchant_id)
            except Exception as e:
                raise HTTPException(502, f"PayPal did not accept the configured credentials: {e}")
            status, detail, scopes = "active", "PayPal sandbox app verified with PayPal.", "orders:read orders:write tracking:write"
        else:
            status, detail, scopes = "active", "Simulated connection: no PayPal sandbox app is configured for this business on this server.", "simulated"
            provider = "paypal_simulated"
    elif provider == "records_import":
        status, detail, scopes = "active", "The business uploads its own order records. They are labelled as reported.", "orders:import catalog:import"
    else:
        raise HTTPException(400, "Supported sources: paypal, records_import.")
    store.run("DELETE FROM merchant_connections WHERE merchant_id = ? AND provider LIKE ?", [merchant_id, provider.split("_")[0] + "%"])
    store.insert("merchant_connections", {"connection_id": str(uuid.uuid4()), "merchant_id": merchant_id, "provider": provider,
                                          "scopes": scopes, "status": status, "detail": detail, "created_at": store.now()})
    store.audit("owner", "connection.create", provider, merchant_id=merchant_id, detail={"scopes": scopes})
    return {"provider": provider, "status": status, "scopes": scopes, "detail": detail}


def _rows(payload) -> list[dict]:
    if isinstance(payload, list):
        return payload
    text = str(payload).lstrip("﻿")
    return [dict(r) for r in csv.DictReader(io.StringIO(text))]


def _evidence(merchant_id: str, kind: str, raw: str, accepted: int, rejected: list) -> str:
    eid = str(uuid.uuid4())
    store.insert("source_evidence", {"evidence_id": eid, "merchant_id": merchant_id, "source": "merchant_import", "kind": kind,
                                     "sha256": hashlib.sha256(raw.encode()).hexdigest(), "rows_accepted": accepted, "rows_rejected": len(rejected),
                                     "status": "validated" if accepted else "rejected", "detail": json.dumps(rejected[:50]), "retrieved_at": store.now()})
    return eid


def import_catalog(merchant_id: str, payload) -> dict:
    rows, accepted, rejected = _rows(payload), 0, []
    with store.transaction():
        for i, r in enumerate(rows, start=1):
            sku = str(r.get("sku") or "").strip()
            try:
                price, stock = float(r.get("price_usd") or r.get("price")), int(float(r.get("stock") or 0))
            except (TypeError, ValueError):
                rejected.append({"row": i, "reason": "price_usd and stock must be numbers"})
                continue
            with store.system():  # SKU ownership is checked across every business
                owner_row = store.one("SELECT merchant_id FROM catalog_items WHERE sku = ?", [sku])
            owner = owner_row or warehouse.one("SELECT merchant_id FROM gold.dim_product WHERE sku = ?", [sku])
            if not sku or not str(r.get("name") or "").strip():
                rejected.append({"row": i, "reason": "sku and name are required"})
            elif price <= 0 or stock < 0:
                rejected.append({"row": i, "reason": "price must be above zero and stock cannot be negative"})
            elif owner and owner["merchant_id"] != merchant_id:
                rejected.append({"row": i, "reason": f"SKU {sku} belongs to another business"})
            else:
                tags = r.get("tags") if isinstance(r.get("tags"), list) else [t.strip() for t in str(r.get("tags") or "").split("|") if t.strip()]
                store.run("DELETE FROM catalog_items WHERE sku = ? AND merchant_id = ?", [sku, merchant_id])
                store.insert("catalog_items", {"sku": sku, "merchant_id": merchant_id, "name": str(r["name"]).strip(), "price_usd": f"{price:.2f}",
                                               "stock": stock, "tags": tags, "description": r.get("description"), "updated_at": store.now()})
                accepted += 1
    eid = _evidence(merchant_id, "catalog", json.dumps(rows, sort_keys=True), accepted, rejected)
    store.audit("owner", "catalog.import", eid, merchant_id=merchant_id, detail={"accepted": accepted, "rejected": len(rejected)})
    return {"accepted": accepted, "rejected": rejected, "evidence_id": eid}


def buyer_key(merchant_id: str, buyer_ref: str) -> str:
    """One-way, per-business key for 'same buyer came back'. The reference itself is never stored."""
    return hmac.new(passport_salt(), f"{merchant_id}:{buyer_ref}".encode(), hashlib.sha256).hexdigest()[:16]


def passport_salt() -> bytes:
    from . import passport
    return bytes.fromhex(passport.keyring()[0]["seed_hex"])[:16]


def import_orders(merchant_id: str, payload, simulated_demo: bool = False) -> dict:
    """Columns: order_id, order_date, amount_usd, status, buyer_ref, refunded_usd, fulfilled_days, tracking_ref, cancelled, dispute, currency."""
    m = store.one("SELECT * FROM merchants WHERE merchant_id = ?", [merchant_id])
    rows, accepted, rejected, seen = _rows(payload), 0, [], set()
    seq = store.one("SELECT coalesce(max(seq), 0) n FROM orders WHERE merchant_id = ?", [merchant_id])["n"]
    today = datetime.date.today()
    truthy = lambda v: str(v).strip().lower() in ("1", "true", "yes", "y")  # noqa: E731
    with store.transaction():
        for i, r in enumerate(rows, start=1):
            oid = f"{merchant_id}:{str(r.get('order_id') or '').strip()}"
            try:
                date = datetime.date.fromisoformat(str(r.get("order_date")).strip())
                amount, refunded = float(r.get("amount_usd")), float(r.get("refunded_usd") or 0)
                days = None if r.get("fulfilled_days") in (None, "") else int(float(r["fulfilled_days"]))
            except (TypeError, ValueError):
                rejected.append({"row": i, "reason": "order_date must be YYYY-MM-DD and amounts must be numbers"})
                continue
            status = str(r.get("status") or "COMPLETED").upper()
            reason = None
            if oid.endswith(":"):
                reason = "order_id is required"
            elif oid in seen or store.one("SELECT 1 FROM orders WHERE order_id = ?", [oid]):
                reason = "duplicate order_id (already imported or repeated in this file)"
            elif str(r.get("currency") or "USD").upper() != "USD":
                reason = "only USD orders are supported"
            elif status not in ("COMPLETED", "PENDING", "VOIDED"):
                reason = "status must be COMPLETED, PENDING or VOIDED"
            elif date > today:
                reason = "order_date is in the future"
            elif amount <= 0 or refunded < 0 or refunded > amount:
                reason = "amount must be above zero and the refund cannot exceed it"
            elif days is not None and days < 0:
                reason = "fulfilled_days cannot be negative"
            elif str(r.get("dispute") or "").lower() not in ("", "lost", "won"):
                reason = "dispute must be empty, lost or won"
            if reason:
                rejected.append({"row": i, "order_id": r.get("order_id"), "reason": reason})
                continue
            seen.add(oid)
            seq += 1
            now, d = store.now(), date.isoformat()
            store.insert("orders", {"order_id": oid, "merchant_id": merchant_id, "seq": seq, "order_date": d, "amount_usd": f"{amount:.2f}",
                                    "status": status, "source_system": "merchant_import", "payer_key": buyer_key(merchant_id, str(r.get("buyer_ref") or oid)),
                                    "item_count": int(float(r.get("item_count") or 1)), "capture_status": "COMPLETED" if status == "COMPLETED" else None,
                                    "simulated": int(simulated_demo), "recorded_at": now})
            ev = lambda prefix, kind, amt: store.insert("payment_events", {  # noqa: E731
                "event_id": f"{prefix}:{oid}", "order_id": oid, "merchant_id": merchant_id, "event_type": kind, "amount_usd": f"{amt:.2f}",
                "event_date": d, "evidence_class": "simulated" if simulated_demo and kind.startswith("dispute") else "merchant_reported", "recorded_at": now})
            fe = lambda prefix, kind, ref=None: store.insert("fulfillment_events", {  # noqa: E731
                "event_id": f"{prefix}:{oid}", "order_id": oid, "merchant_id": merchant_id, "event_type": kind, "days_after_payment": days,
                "reference": ref, "evidence_class": "simulated" if simulated_demo else "merchant_reported", "recorded_at": now})
            ev("cap", "capture", amount)
            if refunded > 0:
                ev("ref", "refund", refunded)
            if str(r.get("dispute") or "").lower() in ("lost", "won"):
                ev("dsp", f"dispute_{str(r['dispute']).lower()}", 0)
            if truthy(r.get("cancelled")):
                fe("can", "cancelled_by_business")
            elif days is not None:
                fe("ful", FULFIL_EVENT[m["business_type"]])
                if str(r.get("tracking_ref") or "").strip() and m["business_type"] == "physical":
                    fe("trk", "tracking_added", str(r["tracking_ref"]).strip())
            accepted += 1
    eid = _evidence(merchant_id, "orders", json.dumps(rows, sort_keys=True, default=str), accepted, rejected)
    store.audit("owner", "orders.import", eid, merchant_id=merchant_id, detail={"accepted": accepted, "rejected": len(rejected)})
    return {"accepted": accepted, "rejected": rejected, "evidence_id": eid,
            "label": "Imported records are labelled 'reported by the business'. They can show a record, but only PayPal-confirmed payments can earn the seal."}


def disclosure_preview(merchant_id: str) -> dict:
    """Exactly what a shopper or an agent would see if the owner publishes now."""
    p = warehouse.one("SELECT * FROM gold.merchant_passport WHERE merchant_id = ?", [merchant_id])
    m = store.one("SELECT passport_published, hidden_metrics FROM merchants WHERE merchant_id = ?", [merchant_id])
    hidden = set(json.loads(m["hidden_metrics"])) if m else set()
    facts = warehouse.rows("""SELECT metric, label, value, unit, numerator, denominator, window_label, evidence_class, is_optional_to_disclose
                              FROM gold.fact_metric_observations WHERE merchant_id = ? ORDER BY display_order""", [merchant_id]) if p else []
    return {"published": bool(m and m["passport_published"]), "has_record": bool(p and p["has_record"]),
            "standing": p["headline"] if p else "No records yet", "verdict": p["verdict"] if p else "Import records or take a PayPal order first.",
            "facts": [{**f, "disclosed": not (f["is_optional_to_disclose"] and f["metric"] in hidden)} for f in facts],
            "never_public": ["individual orders", "buyer names, emails or addresses", "order amounts", "your PayPal credentials"],
            "rule": "You may hide facts marked optional. You cannot hide a fact a rule depends on: that would let a business show only its good side."}


def set_disclosure(merchant_id: str, publish: bool, hidden_metrics: list[str]) -> dict:
    optional = {r["metric"] for r in warehouse.rows("SELECT metric FROM gold.dim_metric WHERE is_optional_to_disclose")}
    bad = [h for h in hidden_metrics if h not in optional]
    if bad:
        raise HTTPException(400, f"These facts cannot be hidden because a rule depends on them or they describe evidence quality: {', '.join(bad)}.")
    store.run("UPDATE merchants SET passport_published = ?, hidden_metrics = ? WHERE merchant_id = ?", [int(publish), json.dumps(sorted(hidden_metrics)), merchant_id])
    store.run("UPDATE consent_grants SET revoked_at = ? WHERE merchant_id = ? AND purpose = 'public_passport' AND revoked_at IS NULL", [store.now(), merchant_id])
    if publish:
        store.insert("consent_grants", {"grant_id": str(uuid.uuid4()), "merchant_id": merchant_id, "purpose": "public_passport", "recipient": "public",
                                        "scope": {"hidden_metrics": sorted(hidden_metrics)}, "consent_version": config.CONSENT_VERSION, "granted_at": store.now()})
    store.audit("owner", "consent.publish" if publish else "consent.withdraw", merchant_id, merchant_id=merchant_id, detail={"hidden": sorted(hidden_metrics)})
    return {"published": publish, "hidden_metrics": sorted(hidden_metrics)}
