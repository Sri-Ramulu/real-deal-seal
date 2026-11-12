"""The coach turns an unmet rule into work the owner can do, and proves the work changed the record.

The demonstrated action is adding a tracking number to a shipped order. In PayPal mode the tracker is sent to
PayPal's Orders API; in every mode the event is recorded as `merchant_reported`, the pipeline is re-run, and the
action stores the metric before and after.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException

from . import config, refresh, store, warehouse

PLAYBOOK = {
    "tracking": ("Add tracking numbers to shipped orders", "is_fulfilled AND NOT has_tracking",
                 "A tracking number on record is evidence a shopper's AI can check. Each one you add raises the rate.", "add_tracking"),
    "fast_ship": ("Ship within 2 days of payment", "is_fulfilled AND NOT fulfilled_within_2_days",
                  "These recent orders left later than 2 days. The rule looks at your last 50 orders, so faster shipping now shows up quickly.", None),
    "completion": ("Record completion for paid jobs", "NOT is_fulfilled AND NOT cancelled_by_business",
                   "These paid jobs have no completion record. If the work was done, record it; if not, finish or refund it.", None),
    "cancellations": ("Cancel fewer confirmed jobs", "cancelled_by_business",
                      "These jobs were cancelled by the business after payment. Check your calendar capacity before accepting bookings.", None),
    "delivery": ("Deliver every paid download", "NOT is_fulfilled",
                 "These sales have no delivery record. Resend the files or check the delivery automation.", None),
    "refunds": ("Look at why these orders were refunded", "is_refunded",
                "Refunds above 8% of recent orders keep the seal away. Check the listings these orders came from.", None),
    "disputes": ("Review the disputes buyers won", "dispute_lost",
                 "A dispute decided for the buyer counts against the business. Reply to open disputes early and keep delivery proof.", None),
    "enough_history": ("Keep selling: the record is still short", "FALSE",
                       "A full record needs 30 completed orders over 60 days. Nothing is wrong; the record just needs time.", None),
}


def plan(merchant_id: str, passport: dict, rules: list[dict]) -> list[dict]:
    actions = []
    for r in rules:
        if r["met"]:
            continue
        title, cond, why, kind = PLAYBOOK[r["rule"]]
        ids = [x["order_id"] for x in warehouse.rows(
            f"SELECT order_id FROM gold.fact_orders WHERE merchant_id = ? AND in_recent_window AND {cond} ORDER BY order_date DESC", [merchant_id])]
        needed = None
        if r["denominator"] and r["comparison"] == ">=":
            needed = max(0, -(-r["threshold"] * r["denominator"] // 100) - (r["numerator"] or 0))
        actions.append({"rule": r["rule"], "title": title, "why": why, "rule_label": r["rule_label"], "can_do_here": kind,
                        "now": f"{r['measured_value']}%" if r["rule"] != "enough_history" else f"{passport['orders_completed']} orders over {passport['history_days']} days",
                        "to_meet_rule": f"{needed} more would meet the rule" if needed else None,
                        "orders_to_review": len(ids), "order_ids": ids})
    if passport["evidence_basis"] != "paypal_record" and passport["has_record"]:
        actions.insert(0, {"rule": "evidence_basis", "title": "Take payments through PayPal to confirm your record", "can_do_here": None,
                           "why": "Your facts come from your own imported records. They show a record, but only payments PayPal confirms can earn the seal.",
                           "rule_label": "Seal requires PayPal-confirmed payments", "now": f"{passport['confirmed_payment_pct']}% confirmed",
                           "to_meet_rule": None, "orders_to_review": 0, "order_ids": []})
    return actions


def history(merchant_id: str) -> list[dict]:
    return store.q("SELECT * FROM coach_actions WHERE merchant_id = ? ORDER BY created_at DESC LIMIT 20", [merchant_id])


def add_tracking(merchant_id: str, order_id: str, tracking_number: str, carrier: str = "OTHER") -> dict:
    tracking_number = tracking_number.strip()
    if not 6 <= len(tracking_number) <= 40:
        raise HTTPException(400, "Enter the carrier's tracking number (6 to 40 characters).")
    order = warehouse.one("SELECT * FROM gold.fact_orders WHERE order_id = ? AND merchant_id = ?", [order_id, merchant_id])
    if not order:
        store.audit("owner", "coach.add_tracking", order_id, "denied", merchant_id=merchant_id, detail={"reason": "not this business's order"})
        raise HTTPException(404, "That order is not in this business's record.")
    if not order["is_fulfilled"]:
        raise HTTPException(409, "That order has not shipped yet, so there is nothing to track.")
    if order["has_tracking"]:
        raise HTTPException(409, "That order already has a tracking number.")
    before = warehouse.one("SELECT value, numerator, denominator FROM gold.fact_metric_observations WHERE merchant_id = ? AND metric = 'tracking_rate'", [merchant_id])
    sent_to_paypal = False
    if config.paypal_credentials(merchant_id) and order["source_system"].startswith("paypal") and order["capture_id"]:
        from . import checkout
        checkout._paypal(merchant_id, "POST", f"/v2/checkout/orders/{order_id}/track", request_id="trk-" + order_id,
                         body={"capture_id": order["capture_id"], "tracking_number": tracking_number, "carrier": carrier, "notify_payer": False})
        sent_to_paypal = True
    action_id = str(uuid.uuid4())
    with store.transaction():
        store.insert("fulfillment_events", {"event_id": f"trk:{order_id}", "order_id": order_id, "merchant_id": merchant_id, "event_type": "tracking_added",
                                            "days_after_payment": order["fulfil_days"], "reference": tracking_number, "evidence_class": "merchant_reported",
                                            "recorded_at": store.now()})
        store.insert("coach_actions", {"action_id": action_id, "merchant_id": merchant_id, "rule": "tracking", "kind": "add_tracking", "target_order_id": order_id,
                                       "status": "recorded", "before_value": f"{before['numerator']} of {before['denominator']} ({before['value']}%)",
                                       "detail": "sent to PayPal" if sent_to_paypal else "recorded here only (no PayPal sandbox credentials on this server)",
                                       "created_at": store.now()})
    result = refresh.run("coach.add_tracking")
    after = warehouse.one("SELECT value, numerator, denominator FROM gold.fact_metric_observations WHERE merchant_id = ? AND metric = 'tracking_rate'", [merchant_id])
    verified = result["ok"] and after["numerator"] == before["numerator"] + 1
    store.run("UPDATE coach_actions SET status = ?, after_value = ?, verified_at = ? WHERE action_id = ?",
              ["verified" if verified else "recorded", f"{after['numerator']} of {after['denominator']} ({after['value']}%)", store.now(), action_id])
    store.audit("owner", "coach.add_tracking", order_id, merchant_id=merchant_id, detail={"sent_to_paypal": sent_to_paypal, "verified": verified})
    return {"action_id": action_id, "verified": verified, "sent_to_paypal": sent_to_paypal,
            "before": before, "after": after, "evidence_class": "merchant_reported",
            "note": "The tracking number is the business's own report. It is labelled that way on the passport; it is not a carrier-confirmed delivery."}
