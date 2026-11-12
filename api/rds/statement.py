"""Business Readiness: a signed statement of records the owner can share with one named recipient, and take back.

An evidence record, not a lending decision. No credit score, no eligibility, no advice.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import secrets
import uuid

from fastapi import HTTPException

from . import config, passport, store, warehouse


def build(merchant_id: str) -> dict | None:
    p = warehouse.one("SELECT * FROM gold.merchant_passport WHERE merchant_id = ? AND has_record", [merchant_id])
    if not p:
        return None
    months = warehouse.rows("""SELECT year_month, orders, CAST(round(captured_usd) AS BIGINT) captured_usd, CAST(round(refunded_usd) AS BIGINT) refunded_usd,
                                      CAST(round(net_usd) AS BIGINT) net_usd, refunded_orders, paypal_confirmed_orders
                               FROM gold.fact_monthly_sales WHERE merchant_id = ? ORDER BY year_month""", [merchant_id])
    rules = warehouse.rows("SELECT rule_label, met FROM gold.fact_rule_results WHERE merchant_id = ? ORDER BY rule_order", [merchant_id])
    done = store.q("SELECT kind, target_order_id, before_value, after_value, verified_at FROM coach_actions WHERE merchant_id = ? AND status = 'verified' ORDER BY verified_at", [merchant_id])
    subject = {
        "id": f"urn:rds:merchant:{merchant_id}", "name": p["merchant_name"], "businessType": p["business_type"], "dataAsOf": p["data_as_of"],
        "statementType": "Statement of commercial records",
        "totals": {"orders": sum(m["orders"] for m in months), "capturedUsd": sum(m["captured_usd"] for m in months),
                   "refundedUsd": sum(m["refunded_usd"] for m in months), "netUsd": sum(m["net_usd"] for m in months),
                   "paypalConfirmedOrders": sum(m["paypal_confirmed_orders"] for m in months)},
        "months": [{"month": m["year_month"], "orders": m["orders"], "capturedUsd": m["captured_usd"], "refundedUsd": m["refunded_usd"],
                    "netUsd": m["net_usd"], "refundedOrders": m["refunded_orders"], "paypalConfirmedOrders": m["paypal_confirmed_orders"]} for m in months],
        "standing": p["headline"], "evidenceBasis": p["evidence_basis"],
        "rules": [{"rule": r["rule_label"], "met": r["met"]} for r in rules],
        "correctiveActions": [{"action": a["kind"], "before": a["before_value"], "after": a["after_value"], "verifiedAt": a["verified_at"]} for a in done],
        "limitations": passport.limitations(p) + [
            "Monthly amounts are rounded to whole US dollars; totals are the sum of the rounded months.",
            "This is a statement of records. It is not a credit score, a lending decision or a statement of eligibility for anything."],
    }
    return passport._envelope("RealDealSealSalesStatement", subject, datetime.date.fromisoformat(p["data_as_of"]))


def share(merchant_id: str, recipient: str, purpose: str) -> dict:
    """Consent for one recipient and one purpose. Returns a link token once; only its hash is stored."""
    if len(recipient.strip()) < 2 or len(purpose.strip()) < 3:
        raise HTTPException(400, "Name who the statement is for and what it is for.")
    doc = build(merchant_id)
    if not doc:
        raise HTTPException(409, "There are no records to state yet.")
    cred = passport.sign(doc)
    existing = store.one("SELECT credential_id FROM credentials WHERE credential_id = ?", [cred["id"]])
    if not existing:
        store.run("UPDATE credentials SET status = 'superseded', status_reason = 'A newer statement was issued.' WHERE merchant_id = ? AND kind = 'statement' AND status = 'active'", [merchant_id])
        passport.register(cred, merchant_id, "statement")
    token = secrets.token_urlsafe(24)
    grant_id = str(uuid.uuid4())
    store.insert("consent_grants", {"grant_id": grant_id, "merchant_id": merchant_id, "purpose": purpose.strip(), "recipient": recipient.strip(),
                                    "scope": {"credential_id": cred["id"], "kind": "sales_statement"}, "consent_version": config.CONSENT_VERSION,
                                    "share_token_hash": hashlib.sha256(token.encode()).hexdigest(), "granted_at": store.now()})
    store.audit("owner", "consent.share_statement", grant_id, merchant_id=merchant_id, detail={"recipient": recipient, "purpose": purpose})
    return {"grant_id": grant_id, "share_url": f"{config.PUBLIC_URL}/statement?token={token}", "recipient": recipient.strip(), "purpose": purpose.strip()}


def grants(merchant_id: str) -> list[dict]:
    return store.q("""SELECT grant_id, purpose, recipient, granted_at, revoked_at FROM consent_grants
                      WHERE merchant_id = ? AND share_token_hash IS NOT NULL ORDER BY granted_at DESC""", [merchant_id])


def revoke(merchant_id: str, grant_id: str) -> dict:
    n = store.run("UPDATE consent_grants SET revoked_at = ? WHERE grant_id = ? AND merchant_id = ? AND revoked_at IS NULL", [store.now(), grant_id, merchant_id])
    if not n:
        raise HTTPException(404, "No active share with that id.")
    store.audit("owner", "consent.revoke_statement", grant_id, merchant_id=merchant_id)
    return {"revoked": True}


def open_shared(token: str) -> dict:
    g = store.one("SELECT * FROM consent_grants WHERE share_token_hash = ?", [hashlib.sha256(token.encode()).hexdigest()])
    if not g or g["revoked_at"]:
        store.audit("recipient", "statement.open", result="denied", merchant_id=g["merchant_id"] if g else None)
        raise HTTPException(403 if g else 404, "The business withdrew this share." if g else "This link is not valid.")
    c = store.one("SELECT document FROM credentials WHERE credential_id = ?", [json.loads(g["scope"])["credential_id"]])
    store.audit(g["recipient"], "statement.open", g["grant_id"], merchant_id=g["merchant_id"])
    cred = json.loads(c["document"])
    return {"recipient": g["recipient"], "purpose": g["purpose"], "granted_at": g["granted_at"], "statement": cred, "check": passport.verify(cred)}
