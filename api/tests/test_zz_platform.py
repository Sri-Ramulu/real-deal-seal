"""End-to-end platform behaviour: tenancy, onboarding, consent, credentials, coach, statements, payments, webhooks.

These tests change records and re-run the pipeline, so they run last (file name) and use Martha, Priscilla and
freshly created workspaces rather than Lydia, whose figures earlier tests pin.
"""
import threading
from pathlib import Path

import pytest

from rds import checkout, config, passport, refresh, store, warehouse, webhooks

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def _workspace(client, name, btype, email):
    r = client.post("/api/onboarding/workspaces", json={"name": name, "business_type": btype, "email": email, "password": "long-enough-1", "category": "Test"})
    assert r.status_code == 200, r.text
    return r.json()["merchant_id"], {"Authorization": f"Bearer {r.json()['token']}"}


# ---- tenancy -------------------------------------------------------------------------------------------------------
def test_one_business_cannot_read_another_businesss_evidence(client, owner):
    r = client.get("/api/studio/lydia/evidence", headers=owner("martha"))
    assert r.status_code == 403
    denied = [e for e in store.recent_audit(20, "lydia") if e["action"] == "access.denied"]
    assert denied and "studio/lydia/evidence" in denied[0]["target"]


def test_one_business_cannot_change_another_businesss_records(client, owner):
    h = owner("martha")
    assert client.post("/api/studio/lydia/disclosure", json={"publish": False}, headers=h).status_code == 403
    assert client.post("/api/studio/lydia/coach/add-tracking", json={"order_id": "x", "tracking_number": "1Z999AA10123456784"}, headers=h).status_code == 403
    assert client.post("/api/studio/lydia/orders/import", json={"rows": []}, headers=h).status_code == 403


def test_a_business_cannot_add_tracking_to_someone_elses_order(client, owner):
    lydia_order = warehouse.one("SELECT order_id FROM gold.fact_orders WHERE merchant_id = 'lydia' AND is_fulfilled AND NOT has_tracking LIMIT 1")["order_id"]
    r = client.post("/api/studio/martha/coach/add-tracking", json={"order_id": lydia_order, "tracking_number": "1Z999AA10123456784"}, headers=owner("martha"))
    assert r.status_code == 404


def test_private_routes_need_a_session(client):
    for path in ("/api/studio/martha", "/api/studio/martha/operations", "/api/studio/martha/statement", "/api/studio/martha/disclosure"):
        assert client.get(path).status_code == 401


def test_wrong_password_is_refused_and_audited(client):
    assert client.post("/api/auth/login", json={"email": "lydia@demo.realdealseal.example", "password": "nope"}).status_code == 401
    assert store.recent_audit(5)[0]["result"] == "denied"


# ---- onboarding a new business with no code change ------------------------------------------------------------------
def test_a_service_business_joins_and_is_judged_by_service_rules(client):
    mid, h = _workspace(client, "Bright Clean Co.", "services", "owner@bright-clean.example")
    assert client.get(f"/api/merchants/{mid}").status_code == 404          # nothing public before consent
    assert client.post(f"/api/studio/{mid}/connect/records_import", headers=h).json()["status"] == "active"
    cat = client.post(f"/api/studio/{mid}/catalog/import", json={"csv": (SAMPLES / "bright-clean.catalog.csv").read_text()}, headers=h).json()
    imp = client.post(f"/api/studio/{mid}/orders/import", json={"csv": (SAMPLES / "bright-clean.orders.csv").read_text(), "simulated_demo": True}, headers=h).json()
    assert cat["accepted"] == 3 and imp["accepted"] == 46 and imp["rejected"] == [] and imp["refresh"]["ok"]
    s = client.get(f"/api/studio/{mid}", headers=h).json()
    assert {r["rule"] for r in s["rules"]} == {"enough_history", "completion", "cancellations", "disputes", "refunds"}
    assert not {"tracking_rate", "fast_ship_rate"} & {f["metric"] for f in s["facts"]}   # no parcel rules for a cleaner
    assert s["passport"]["standing"] == "reported" and s["passport"]["evidence_basis"] == "merchant_import"
    assert s["coach"][0]["rule"] == "evidence_basis"
    # still invisible to shoppers and agents until the owner publishes
    assert mid not in {m["merchant_id"] for m in client.get("/api/merchants").json()}
    assert not [o for o in client.get("/api/products").json() if o["shop_id"] == mid]
    client.post(f"/api/studio/{mid}/disclosure", json={"publish": True, "hidden_metrics": []}, headers=h)
    pub = client.get(f"/api/merchants/{mid}").json()
    assert pub["passport"]["headline"] == "Self-reported record, not yet confirmed" and pub["seal"]["credentialSubject"]["evidenceBasis"] == "merchant_import"
    assert any("cannot earn the seal" in l for l in pub["seal"]["credentialSubject"]["limitations"])
    assert [o for o in client.get("/api/products?q=deep clean").json() if o["shop_id"] == mid]


def test_imported_records_can_never_earn_the_seal(client):
    assert warehouse.one("SELECT count(*) n FROM gold.merchant_passport WHERE standing = 'sealed' AND evidence_basis <> 'paypal_record'")["n"] == 0
    p = warehouse.one("SELECT standing, rules_met, rules_total, confirmed_payment_pct FROM gold.merchant_passport WHERE merchant_id = 'bright-clean-co'")
    assert p["standing"] == "reported" and p["confirmed_payment_pct"] == 0


def test_a_digital_business_is_judged_on_delivery_not_shipping(client):
    mid, h = _workspace(client, "Pixel Press Studio", "digital", "owner@pixel-press.example")
    client.post(f"/api/studio/{mid}/orders/import", json={"csv": (SAMPLES / "pixel-press.orders.csv").read_text(), "simulated_demo": True}, headers=h)
    s = client.get(f"/api/studio/{mid}", headers=h).json()
    assert {r["rule"] for r in s["rules"]} == {"enough_history", "delivery", "disputes", "refunds"}
    delivery = next(r for r in s["rules"] if r["rule"] == "delivery")
    assert (delivery["numerator"], delivery["denominator"], delivery["met"]) == (31, 38, False)
    assert s["coach"][1]["rule"] == "delivery" and s["coach"][1]["orders_to_review"] == 7


def test_import_validation_rejects_bad_rows_and_says_why(client):
    mid, h = _workspace(client, "Messy Books", "physical", "owner@messy.example")
    rows = [{"order_id": "A1", "order_date": "2026-09-01", "amount_usd": 20, "fulfilled_days": 1, "tracking_ref": "TRK12345"},
            {"order_id": "A1", "order_date": "2026-09-02", "amount_usd": 20},                       # duplicate
            {"order_id": "A2", "order_date": "2026-09-03", "amount_usd": 20, "currency": "EUR"},     # wrong currency
            {"order_id": "A3", "order_date": "2999-01-01", "amount_usd": 20},                       # future
            {"order_id": "A4", "order_date": "2026-09-04", "amount_usd": 20, "refunded_usd": 25},    # refund above amount
            {"order_id": "A5", "order_date": "not a date", "amount_usd": 20},                       # unparseable
            {"order_id": "", "order_date": "2026-09-05", "amount_usd": 20}]                          # no id
    out = client.post(f"/api/studio/{mid}/orders/import", json={"rows": rows}, headers=h).json()
    assert out["accepted"] == 1 and [r["row"] for r in out["rejected"]] == [2, 3, 4, 5, 6, 7]
    assert "duplicate" in out["rejected"][0]["reason"] and "USD" in out["rejected"][1]["reason"]
    again = client.post(f"/api/studio/{mid}/orders/import", json={"rows": rows[:1]}, headers=h).json()
    assert again["accepted"] == 0 and "duplicate" in again["rejected"][0]["reason"]             # re-import is idempotent
    p = client.get(f"/api/studio/{mid}", headers=h).json()["passport"]
    assert p["standing"] == "new" and p["orders_completed"] == 1                                 # one order is 'new', never 'bad'


def test_catalog_import_cannot_take_over_another_businesss_sku(client):
    mid, h = _workspace(client, "Sku Squatter", "physical", "owner@squat.example")
    out = client.post(f"/api/studio/{mid}/catalog/import", json={"rows": [{"sku": "JF-RUN-PD", "name": "Fake runner", "price_usd": 1, "stock": 5}]}, headers=h).json()
    assert out["accepted"] == 0 and "another business" in out["rejected"][0]["reason"]
    assert warehouse.one("SELECT merchant_id, price_usd FROM gold.dim_product WHERE sku = 'JF-RUN-PD'") == {"merchant_id": "lydia", "price_usd": 36}


def test_an_empty_workspace_explains_what_is_missing(client):
    mid, h = _workspace(client, "Brand New Bakery", "local", "owner@bakery.example")
    s = client.get(f"/api/studio/{mid}", headers=h).json()
    assert s["facts"] == [] and "Import orders" in s["pending"]
    d = client.get(f"/api/studio/{mid}/disclosure", headers=h).json()
    assert d["has_record"] is False and "individual orders" in d["never_public"]


# ---- consent and credentials ------------------------------------------------------------------------------------------
def test_owner_can_hide_optional_facts_but_never_a_rule_fact(client, owner):
    h = owner("martha")
    assert client.post("/api/studio/martha/disclosure", json={"publish": True, "hidden_metrics": ["refund_rate"]}, headers=h).status_code == 400
    old = client.get("/api/merchants/martha/seal").json()
    client.post("/api/studio/martha/disclosure", json={"publish": True, "hidden_metrics": ["sales_net_usd"]}, headers=h)
    pub = client.get("/api/merchants/martha").json()
    assert "sales_net_usd" not in {f["metric"] for f in pub["facts"]} and pub["passport"]["net_sales_usd"] is None
    assert pub["seal"]["credentialSubject"]["notDisclosed"] == ["sales_net_usd"] and pub["seal"]["id"] != old["id"]
    assert client.post("/api/verify", json={"credential": old}).json()["result"] == "superseded"
    assert client.post("/api/verify", json={"credential": pub["seal"]}).json()["result"] == "genuine"
    client.post("/api/studio/martha/disclosure", json={"publish": True, "hidden_metrics": []}, headers=h)


def test_withdrawing_consent_revokes_the_passport_and_hides_the_record(client, owner):
    h = owner("priscilla")
    cred = client.get("/api/merchants/priscilla/seal").json()
    client.post("/api/studio/priscilla/disclosure", json={"publish": False}, headers=h)
    page = client.get("/api/merchants/priscilla").json()            # shown as withdrawn, never as an unknown shop
    assert page["withdrawn"] and page["facts"] == [] and page["products"] == [] and page["passport"]["standing"] == "withdrawn"
    assert client.post("/api/verify", json={"credential": cred}).json()["result"] == "withdrawn"
    assert not [o for o in client.get("/api/products").json() if o["shop_id"] == "priscilla"]
    tool = client.post("/api/tools/get_merchant_passport", json={"shop_id": "priscilla"}).json()
    assert tool["found"] and tool["do_not_recommend"] and tool["withdrawn_by"] == "the business itself" and "facts" not in tool
    assert client.get(f"/api/credentials/status?id={cred['id']}").json()["status"] == "revoked"
    client.post("/api/studio/priscilla/disclosure", json={"publish": True}, headers=h)
    assert client.post("/api/verify", json={"credential": client.get("/api/merchants/priscilla/seal").json()}).json()["genuine"]


def test_key_rotation_keeps_old_seals_valid_and_revocation_kills_them():
    before = passport.issue("martha")
    new_key = passport.rotate_key()
    assert passport.verify(before)["result"] == "genuine"                      # retired key still verifies
    after = passport.sign(passport.build("martha"))
    assert after["proof"]["verificationMethod"].endswith(new_key) and passport.verify(after)["result"] in ("genuine", "superseded")
    assert len(passport.did_document()["verificationMethod"]) == 2
    passport.revoke_key("key-1")
    assert passport.verify(before)["result"] == "forged"                       # everything a revoked key signed fails
    refresh.reconcile_credentials()


def test_refreshing_twice_issues_nothing_new():
    refresh.run("test")
    assert refresh.run("test")["credentials"]["issued"] == 0


def test_a_red_pipeline_keeps_the_last_good_warehouse(monkeypatch):
    from rdsp import runner
    good = warehouse.catalog()["run_id"]
    monkeypatch.setattr(runner, "build", lambda **k: (_ for _ in ()).throw(runner.GateFailed("gate 4 (contracts) failed: test")))
    out = refresh.run("broken")
    assert out["ok"] is False and "gate 4" in out["error"]
    assert warehouse.catalog()["run_id"] == good and warehouse.one("SELECT count(*) n FROM gold.merchant_passport")["n"] > 0
    assert store.one("SELECT status FROM jobs ORDER BY job_id DESC LIMIT 1")["status"] == "failed"


# ---- coach: an action that changes the record -------------------------------------------------------------------------
def test_adding_tracking_raises_the_rate_and_is_recorded_before_and_after(client, owner):
    h = owner("martha")
    todo = next(a for a in client.get("/api/studio/martha", headers=h).json()["coach"] if a["rule"] == "tracking")
    assert todo["can_do_here"] == "add_tracking" and todo["orders_to_review"] == 9
    out = client.post("/api/studio/martha/coach/add-tracking", json={"order_id": todo["order_ids"][0], "tracking_number": "1Z999AA10123456784", "carrier": "UPS"}, headers=h).json()
    assert out["verified"] and (out["before"]["numerator"], out["after"]["numerator"]) == (39, 40) and out["evidence_class"] == "merchant_reported"
    assert out["sent_to_paypal"] is False
    again = client.post("/api/studio/martha/coach/add-tracking", json={"order_id": todo["order_ids"][0], "tracking_number": "1Z999AA10123456784"}, headers=h)
    assert again.status_code == 409
    hist = client.get("/api/studio/martha", headers=h).json()["coach_history"][0]
    assert hist["status"] == "verified" and hist["before_value"].startswith("39 of 48") and hist["after_value"].startswith("40 of 48")
    fact = next(f for f in client.get("/api/merchants/martha").json()["facts"] if f["metric"] == "tracking_rate")
    assert fact["numerator"] == 40 and fact["evidence_class"] == "merchant_reported"


# ---- business readiness statement ---------------------------------------------------------------------------------------
def test_statement_totals_reconcile_and_limits_stay_visible(client, owner):
    st = client.get("/api/studio/martha/statement", headers=owner("martha")).json()["statement"]
    s = st["credentialSubject"]
    assert s["totals"]["netUsd"] == sum(m["netUsd"] for m in s["months"]) and s["totals"]["orders"] == 60
    assert abs(s["totals"]["netUsd"] - warehouse.one("SELECT sum(net_usd) n FROM gold.fact_orders WHERE merchant_id = 'martha'")["n"]) <= len(s["months"])
    assert any("not a credit score" in l for l in s["limitations"]) and any("simulated" in l for l in s["limitations"])
    assert s["correctiveActions"] and passport.verify(st)["result"] in ("genuine", "superseded")


def test_statement_is_shared_with_one_recipient_and_can_be_taken_back(client, owner):
    h = owner("martha")
    share = client.post("/api/studio/martha/statement/share", json={"recipient": "Harbor Community Bank", "purpose": "Account review"}, headers=h).json()
    token = share["share_url"].split("token=")[1]
    opened = client.get(f"/api/statements/{token}").json()
    assert opened["recipient"] == "Harbor Community Bank" and opened["check"]["genuine"] and opened["statement"]["credentialSubject"]["totals"]["orders"] == 60
    assert client.get("/api/statements/not-a-real-token").status_code == 404
    client.post(f"/api/studio/martha/statement/shares/{share['grant_id']}/revoke", headers=h)
    assert client.get(f"/api/statements/{token}").status_code == 403
    assert [e["action"] for e in store.recent_audit(10, "martha")].count("statement.open") >= 2   # every open, allowed or not, is logged


# ---- payments: write-back, refunds, concurrency, webhooks -------------------------------------------------------------
@pytest.fixture()
def paypal(monkeypatch):
    """Stand-in for PayPal's API so the real-mode path, including the pipeline refresh, runs end to end."""
    state = {"calls": [], "verify": "SUCCESS"}

    def api(merchant_id, method, path, request_id=None, body=None):
        state["calls"].append((method, path))
        if path == "/v2/checkout/orders":
            state["amount"] = body["purchase_units"][0]["amount"]["value"]
            return {"id": "PP-" + request_id[:8].upper(), "status": "PAYER_ACTION_REQUIRED", "links": [{"rel": "payer-action", "href": "https://www.sandbox.paypal.com/checkoutnow?token=X"}]}
        if path.endswith("/verify-webhook-signature"):
            return {"verification_status": state["verify"]}
        if path.endswith("/refund"):
            return {"id": "RF-" + path.split("/")[-2], "status": "COMPLETED"}
        if path.endswith("/track"):
            return {"id": "ok"}
        if method == "GET":
            return {"id": path.rsplit("/", 1)[1], "status": "APPROVED", "payer": {"payer_id": "BUYER42"}, "purchase_units": [{}]}
        return {"status": "COMPLETED", "payer": {"payer_id": "BUYER42"}, "purchase_units": [{"payments": {"captures": [
            {"id": "CAP-" + path.split("/")[-2], "status": "COMPLETED", "amount": {"value": state["amount"], "currency_code": "USD"}}]}}]}

    monkeypatch.setattr(config, "paypal_credentials", lambda m: ("id", "secret"))
    monkeypatch.setattr(config, "PAYPAL_WEBHOOK_ID", "WH-1")
    monkeypatch.setattr(checkout, "_paypal", api)
    return state


def test_a_confirmed_paypal_order_joins_the_record_and_a_refund_recalculates_it(client, owner, paypal):
    before = warehouse.one("SELECT orders_completed, refund_pct FROM gold.merchant_passport WHERE merchant_id = 'priscilla'")
    s = checkout.create("PR-TOT-CN", 1)
    done = checkout.complete(s["paypal_order_id"])
    assert done["status"] == "CAPTURED"
    row = warehouse.one("SELECT source_system, payment_evidence_class, capture_id FROM gold.fact_orders WHERE order_id = ?", [s["paypal_order_id"]])
    assert row == {"source_system": "paypal_checkout", "payment_evidence_class": "paypal_sandbox_confirmed", "capture_id": done["capture_id"]}
    after = warehouse.one("SELECT orders_completed, evidence_basis FROM gold.merchant_passport WHERE merchant_id = 'priscilla'")
    assert after == {"orders_completed": before["orders_completed"] + 1, "evidence_basis": "paypal_record"}
    # refund after the credential was issued: the dependent metric recalculates and the old passport is superseded
    old = passport.issue("priscilla")
    r = client.post(f"/api/studio/priscilla/orders/{s['paypal_order_id']}/refund", headers=owner("priscilla")).json()
    assert r["refunded"] and ("POST", f"/v2/payments/captures/{done['capture_id']}/refund") in paypal["calls"]
    fact = warehouse.one("SELECT numerator, denominator FROM gold.fact_metric_observations WHERE merchant_id = 'priscilla' AND metric = 'refund_rate'")
    assert fact["numerator"] == 1 and passport.verify(old)["result"] == "superseded"
    assert client.post(f"/api/studio/priscilla/orders/{s['paypal_order_id']}/refund", headers=owner("priscilla")).status_code == 409


def test_a_simulated_checkout_never_becomes_evidence():
    n = warehouse.one("SELECT orders_completed n FROM gold.merchant_passport WHERE merchant_id = 'martha'")["n"]
    s = checkout.create("MA-APR-RD", 1)
    assert s["mode"] == "simulated" and checkout.complete(s["paypal_order_id"])["status"] == "CAPTURED"
    refresh.run("test")
    assert warehouse.one("SELECT orders_completed n FROM gold.merchant_passport WHERE merchant_id = 'martha'")["n"] == n
    assert store.one("SELECT source_system FROM orders WHERE order_id = ?", [s["paypal_order_id"]])["source_system"] == "simulated_checkout"


def test_two_buyers_racing_for_the_last_unit_cannot_both_capture():
    sku = "MA-BRD-WL"
    while checkout.available_stock(sku) > 1:                                    # sell down to the last unit
        checkout.complete(checkout.create(sku, min(10, checkout.available_stock(sku) - 1))["paypal_order_id"])
    a, b = checkout.create(sku, 1), checkout.create(sku, 1)                      # both opened while one unit is left
    assert checkout.complete(a["paypal_order_id"])["status"] == "CAPTURED"
    with pytest.raises(checkout.CheckoutError) as e:
        checkout.complete(b["paypal_order_id"])                                 # stale stock: blocked at capture, nothing charged
    assert e.value.code == "out_of_stock" and store.session(b["session_id"])["status"] == "FAILED" and store.session(b["session_id"])["capture_id"] is None
    with pytest.raises(checkout.CheckoutError):
        checkout.create(sku, 1)


def test_ten_simultaneous_returns_capture_once():
    s = checkout.create("MA-MIT-GR", 1)
    results = []
    threads = [threading.Thread(target=lambda: results.append(checkout.complete(s["paypal_order_id"])["status"])) for _ in range(10)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert set(results) <= {"CAPTURED", "CAPTURING"} and store.session(s["session_id"])["status"] == "CAPTURED"
    assert len([e for e in store.recent_audit(300) if e["action"] == "checkout.capture" and e["target"] == s["session_id"]]) == 1


def _event(event_id, kind, order_id, **resource):
    return {"id": event_id, "event_type": kind, "resource": {"id": "RES-" + event_id, "supplementary_data": {"related_ids": {"order_id": order_id}}, **resource}}


def test_webhook_is_processed_only_when_paypal_confirms_it_and_only_once(client, paypal):
    s = checkout.create("MA-TOW-SC", 1)
    ev = _event("WH-EVT-1", "PAYMENT.CAPTURE.COMPLETED", s["paypal_order_id"])
    paypal["verify"] = "FAILURE"
    assert client.post("/api/webhooks/paypal", json=ev).status_code == 400 and store.session(s["session_id"])["status"] == "CREATED"
    paypal["verify"] = "SUCCESS"
    first = client.post("/api/webhooks/paypal", json=ev).json()
    assert first == {"processed": True, "outcome": "CAPTURED"}
    assert client.post("/api/webhooks/paypal", json=ev).json()["reason"].startswith("Duplicate")
    assert len([e for e in store.recent_audit(300) if e["action"] == "checkout.capture" and e["target"] == s["session_id"]]) == 1
    refund = _event("WH-EVT-2", "PAYMENT.CAPTURE.REFUNDED", s["paypal_order_id"], amount={"value": s["amount_usd"]})
    assert client.post("/api/webhooks/paypal", json=refund).json()["outcome"] == "refund recorded"
    refund["id"] = "WH-EVT-3"                                                    # PayPal re-sends under a new event id, same refund resource
    refund["resource"]["id"] = "RES-WH-EVT-2"
    assert client.post("/api/webhooks/paypal", json=refund).json()["outcome"] == "refund already recorded"
    assert warehouse.one("SELECT refunded_usd, capture_status FROM gold.fact_orders WHERE order_id = ?", [s["paypal_order_id"]])["capture_status"] == "REFUNDED"


def test_webhook_for_an_unknown_order_changes_nothing(client, paypal):
    assert client.post("/api/webhooks/paypal", json=_event("WH-EVT-9", "PAYMENT.CAPTURE.COMPLETED", "NOT-OURS")).json()["processed"] is False


def test_a_denied_capture_webhook_never_shows_as_paid(client, paypal):
    s = checkout.create("MA-RUN-HV", 1)
    client.post("/api/webhooks/paypal", json=_event("WH-EVT-10", "PAYMENT.CAPTURE.DENIED", s["paypal_order_id"]))
    assert store.session(s["session_id"])["status"] == "FAILED" and checkout.complete(s["paypal_order_id"])["status"] == "FAILED"


def test_real_mode_tracking_is_sent_to_paypal(client, owner, paypal):
    o = warehouse.one("SELECT order_id FROM gold.fact_orders WHERE merchant_id = 'martha' AND in_recent_window AND is_fulfilled AND NOT has_tracking LIMIT 1")
    out = client.post("/api/studio/martha/coach/add-tracking", json={"order_id": o["order_id"], "tracking_number": "9400100000000000000000"}, headers=owner("martha")).json()
    assert out["sent_to_paypal"] and ("POST", f"/v2/checkout/orders/{o['order_id']}/track") in paypal["calls"]


# ---- agent-facing safety ----------------------------------------------------------------------------------------------
def test_every_assistant_decision_is_logged(client):
    n = store.one("SELECT count(*) n FROM agent_decisions")["n"]
    client.post("/api/chat", json={"messages": [{"role": "user", "content": "walnut bread board"}]})
    row = store.one("SELECT * FROM agent_decisions ORDER BY at DESC LIMIT 1")
    assert store.one("SELECT count(*) n FROM agent_decisions")["n"] == n + 1 and row["mode"] == "offline" and "search_products" in row["tools"]


def test_agent_tools_never_show_another_businesss_numbers(client):
    a, b = (client.post("/api/tools/get_merchant_passport", json={"shop_id": s}).json() for s in ("lydia", "martha"))
    assert a["shop"] == "Lydia Linen Co." and b["shop"] == "Martha's Kitchen" and a["facts"] != b["facts"]


def test_simulated_history_is_always_labelled(client):
    facts = client.get("/api/merchants/lydia").json()["facts"]
    assert {f["metric"]: f["evidence_class"] for f in facts}["fast_ship_rate"] == "simulated"
    assert any("simulated" in l for l in client.get("/api/merchants/lydia/seal").json()["credentialSubject"]["limitations"])


def test_criteria_are_published_per_business_type(client):
    c = client.get("/api/criteria").json()
    assert set(c["rules_by_business_type"]) == {"physical", "services", "digital"} and len(c["metric_definitions"]) == 13
    assert len(client.get("/api/business-types").json()) == 4
