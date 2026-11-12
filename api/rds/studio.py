"""Merchant Studio (private): everything one business sees about itself. Public pages use `public_passport`."""
from __future__ import annotations

import json

from . import coach, passport, store, warehouse as wh


def public_passport(merchant_id: str) -> dict | None:
    """What anyone may see: aggregated facts only, minus what the owner chose not to disclose."""
    p = wh.one("SELECT * FROM gold.merchant_passport WHERE merchant_id = ? AND (passport_published OR standing = 'withdrawn')", [merchant_id])
    if not p:
        return None
    if not p["passport_published"]:
        # The business took its passport down. Show that it was withdrawn, and nothing else from the record.
        keep = ("merchant_id", "merchant_name", "merchant_kind", "origin", "business_type", "business_type_label", "standing", "headline",
                "verdict", "seal_withdrawn_by", "seal_withdrawn_at", "seal_withdrawn_reason", "passport_published", "has_record")
        return {"passport": {k: p[k] for k in keep} | {"hidden_metrics": [], "has_record": False}, "facts": [], "rules": [], "seal": None,
                "record_shape": None, "products": [], "withdrawn": True}
    facts = wh.rows("""SELECT metric, label, value, unit, numerator, denominator, window_label, evidence_class, layer
                       FROM gold.fact_metric_observations WHERE merchant_id = ? AND NOT (is_optional_to_disclose AND list_contains(?, metric))
                       ORDER BY display_order""", [merchant_id, p["hidden_metrics"]])
    rules = wh.rows("SELECT rule, rule_label, metric, measured_value, numerator, denominator, measured, met FROM gold.fact_rule_results WHERE merchant_id = ? ORDER BY rule_order", [merchant_id])
    hidden = set(p["hidden_metrics"])
    if "sales_net_usd" in hidden:
        p["net_sales_usd"] = None
    if "repeat_buyer_rate" in hidden:
        p["repeat_buyer_pct"] = None
    shape = wh.one("""SELECT count(*) orders, count(*) FILTER (is_refunded) refunded, count(*) FILTER (is_fulfilled) fulfilled,
                             count(*) FILTER (is_fulfilled AND NOT has_tracking) fulfilled_without_tracking, count(*) FILTER (has_dispute) disputed
                      FROM gold.fact_orders WHERE merchant_id = ?""", [merchant_id])
    return {"passport": p, "facts": facts, "rules": rules, "seal": passport.issue(merchant_id), "record_shape": shape,
            "products": wh.rows("SELECT sku, product_name, price_usd, in_stock FROM gold.dim_product WHERE merchant_id = ? ORDER BY sku", [merchant_id])}


def get(merchant_id: str) -> dict | None:
    m = store.one("SELECT * FROM merchants WHERE merchant_id = ?", [merchant_id])
    if not m:
        return None
    p = wh.one("SELECT * FROM gold.merchant_passport WHERE merchant_id = ?", [merchant_id])
    base = {"merchant": {**m, "hidden_metrics": json.loads(m["hidden_metrics"])},
            "connections": store.q("SELECT provider, scopes, status, detail, created_at FROM merchant_connections WHERE merchant_id = ?", [merchant_id]),
            "imports": store.q("SELECT kind, rows_accepted, rows_rejected, status, sha256, retrieved_at FROM source_evidence WHERE merchant_id = ? ORDER BY retrieved_at DESC LIMIT 10", [merchant_id]),
            "catalog": store.q("SELECT sku, name, price_usd, stock FROM catalog_items WHERE merchant_id = ? ORDER BY sku", [merchant_id]),
            "pending": None if p else "Your workspace exists but the record is empty. Import orders, or take a PayPal order, then refresh."}
    if not p or not p["has_record"]:
        return {**base, "passport": p, "facts": [], "rules": [], "coach": [], "monthly": [], "weekly": [], "products": [], "coach_history": [], "seal": None}
    facts = wh.rows("SELECT * FROM gold.fact_metric_observations WHERE merchant_id = ? ORDER BY display_order", [merchant_id])
    rules = wh.rows("SELECT * FROM gold.fact_rule_results WHERE merchant_id = ? ORDER BY rule_order", [merchant_id])
    return {**base, "passport": p, "facts": facts, "rules": rules, "coach": coach.plan(merchant_id, p, rules), "coach_history": coach.history(merchant_id),
            "monthly": wh.measure("commerce_metrics", ["orders", "net_usd", "refund_rate_pct", "fulfilment_rate_pct", "paypal_confirmed_pct"], ["year_month"], {"merchant_id": merchant_id}),
            "weekly": wh.measure("commerce_metrics", ["orders", "net_usd"], ["week_start"], {"merchant_id": merchant_id}),
            "products": wh.rows("SELECT sku, product_name, price_usd, stock FROM gold.dim_product WHERE merchant_id = ? ORDER BY sku", [merchant_id]),
            "seal": passport.issue(merchant_id)}


def evidence(merchant_id: str) -> list[dict]:
    return wh.rows("""SELECT order_id, order_no, invoice_id, order_date, amount_usd, refunded_usd, net_usd, capture_id, capture_status, item_count,
                             fulfil_days, tracker_count, is_fulfilled, has_tracking, fulfilled_within_2_days, cancelled_by_business, is_refunded,
                             has_dispute, dispute_lost, dispute_reason, is_returning_buyer, in_recent_window, history_is_simulated,
                             payment_evidence_class, source_system
                      FROM gold.fact_orders WHERE merchant_id = ? ORDER BY order_date DESC, order_no DESC""", [merchant_id])


def operations(merchant_id: str) -> dict:
    """Orders and Operations: recent orders with their payment and fulfilment events, plus live checkouts."""
    orders = wh.rows("""SELECT order_id, order_no, order_date, amount_usd, capture_status, fulfil_days, is_fulfilled, has_tracking, cancelled_by_business,
                               is_refunded, has_dispute, source_system FROM gold.fact_orders WHERE merchant_id = ? AND recency_rank <= 30 ORDER BY recency_rank""", [merchant_id])
    ful = wh.rows("""SELECT e.order_id, e.event_type, e.days_after_payment, e.reference, e.evidence_class FROM gold.fact_fulfillment_events e
                     JOIN gold.fact_orders f USING (order_id) WHERE f.merchant_id = ? AND f.recency_rank <= 30""", [merchant_id])
    by = {}
    for e in ful:
        by.setdefault(e["order_id"], []).append(e)
    return {"orders": [{**o, "events": by.get(o["order_id"], [])} for o in orders],
            "checkouts": store.q("""SELECT session_id, sku, quantity, amount_usd, mode, status, paypal_order_id, capture_id, created_at
                                    FROM checkout_sessions WHERE merchant_id = ? ORDER BY created_at DESC LIMIT 20""", [merchant_id]),
            "audit": store.recent_audit(25, merchant_id)}
