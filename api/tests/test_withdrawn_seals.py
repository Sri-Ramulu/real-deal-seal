"""A sealed shop that turns out to be a scam.

Real Deal Seal can withdraw one shop's seal for cause. After that the seal fails its check, shoppers and AI agents
see the reason, checkout is off, and nobody else is touched. A shop that takes its own passport down is shown as
withdrawn, never as an unknown shop. Resolved PayPal disputes reach the record through the webhook.
"""
import pytest

from rds import checkout, passport, store, tools, webhooks

TOKEN = "test-admin-token"
REASON = "Unresolved buyer complaints about items that were never delivered."


@pytest.fixture
def admin(monkeypatch):
    monkeypatch.setenv("RDS_ADMIN_TOKEN", TOKEN)
    return {"x-admin-token": TOKEN}


def test_withdrawing_needs_the_admin_token(client, monkeypatch):
    monkeypatch.delenv("RDS_ADMIN_TOKEN", raising=False)
    assert client.post("/api/admin/merchants/lydia/withdraw", json={"reason": REASON}).status_code == 403
    monkeypatch.setenv("RDS_ADMIN_TOKEN", TOKEN)
    assert client.post("/api/admin/merchants/lydia/withdraw", json={"reason": REASON}, headers={"x-admin-token": "wrong"}).status_code == 403


def test_withdraw_for_cause_end_to_end(client, admin):
    old_seal = client.get("/api/merchants/lydia/seal").json()
    assert passport.verify(old_seal)["result"] == "genuine"
    try:
        r = client.post("/api/admin/merchants/lydia/withdraw", json={"reason": REASON}, headers=admin)
        assert r.status_code == 200, r.text
        assert r.json()["passport"]["standing"] == "withdrawn"
        assert client.post("/api/admin/merchants/lydia/withdraw", json={"reason": REASON}, headers=admin).status_code == 409

        # The seal Lydia had been showing stops checking out, with the reason.
        check = passport.verify(old_seal)
        assert check["result"] == "withdrawn"
        assert REASON in str(check)

        # The public page and the shops list say so.
        page = client.get("/api/merchants/lydia").json()
        assert page["passport"]["standing"] == "withdrawn" and REASON in page["passport"]["verdict"] and page["seal"] is None
        listed = {m["merchant_id"]: m for m in client.get("/api/merchants").json()}
        assert listed["lydia"]["headline"] == "Seal withdrawn"
        assert passport.verify(client.get("/api/merchants/lydia/seal").json())["result"] == "withdrawn", "the last seal is shown failing the check"

        # The AI is told, by id and by name, and never sees an unknown shop.
        for res in (tools.get_merchant_passport("lydia"), tools.check_any_shop("Lydia Linen Co.")):
            assert res["found"] and res["do_not_recommend"] and res["reason"] == REASON and res["withdrawn_by"] == "Real Deal Seal"
        offers = [o for o in tools.search_products("linen napkins")["offers"] if o["shop_id"] == "lydia"]
        assert offers and all(o["shop_standing"] == "Seal withdrawn" and not o["paypal_checkout"] for o in offers)

        # No checkout, from the page or from the agent.
        r = client.post("/api/checkout", json={"sku": "JF-CUS-PL", "quantity": 1})
        assert r.status_code in (400, 409) and r.json()["error"] == "seal_withdrawn"
        assert tools.create_checkout("JF-CUS-PL")["created"] is False

        # Nobody else is touched.
        assert client.get("/api/merchants/martha").json()["passport"]["standing"] != "withdrawn"
        assert passport.verify(client.get("/api/merchants/priscilla/seal").json())["result"] == "genuine"
    finally:
        r = client.post("/api/admin/merchants/lydia/reinstate", json={"note": "Test finished."}, headers=admin)
    assert r.status_code == 200 and r.json()["passport"]["standing"] == "sealed"
    assert passport.verify(client.get("/api/merchants/lydia/seal").json())["result"] == "genuine"
    # The old copy is either valid again (same facts, same document) or withdrawn (facts moved on); it is never "unknown".
    assert passport.verify(old_seal)["result"] in ("genuine", "withdrawn")
    assert client.post("/api/admin/merchants/lydia/reinstate", json={"note": "Again."}, headers=admin).status_code == 409


def test_a_shop_that_takes_its_passport_down_is_shown_as_withdrawn_not_unknown(client, owner):
    h = owner("martha")
    try:
        r = client.post("/api/studio/martha/disclosure", json={"publish": False, "hidden_metrics": []}, headers=h)
        assert r.status_code == 200, r.text
        res = tools.get_merchant_passport("martha")
        assert res["found"] and res["do_not_recommend"] and res["withdrawn_by"] == "the business itself"
        assert "facts" not in res, "a business that withdrew its passport keeps its facts private"
        assert tools.check_any_shop("Martha's Kitchen")["standing"] == "Seal withdrawn"
        page = client.get("/api/merchants/martha").json()
        assert page["withdrawn"] and page["facts"] == [] and page["passport"]["headline"] == "Seal withdrawn"
        assert not any(o["shop_id"] == "martha" for o in tools.search_products("kitchen towels")["offers"])
    finally:
        client.post("/api/studio/martha/disclosure", json={"publish": True, "hidden_metrics": []}, headers=h)
    assert tools.get_merchant_passport("martha")["standing"] != "Seal withdrawn"


def test_a_resolved_paypal_dispute_reaches_the_record(monkeypatch, client):
    session = {"session_id": "s1", "merchant_id": "lydia", "paypal_order_id": "ORDER-1"}
    monkeypatch.setattr(store, "session_by", lambda col, val: session if (col, val) == ("capture_id", "CAP-9") else None)
    monkeypatch.setattr(webhooks, "verify_with_paypal", lambda *a: True)
    seen = []
    monkeypatch.setattr(checkout, "record_dispute", lambda order_id, won, amount, dispute_id, source: seen.append((order_id, won, amount, dispute_id)) or True)
    event = {"id": "WH-dispute-1", "event_type": "CUSTOMER.DISPUTE.RESOLVED",
             "resource": {"id": "PP-D-1", "disputed_transactions": [{"seller_transaction_id": "CAP-9"}],
                          "dispute_amount": {"value": "32.00"}, "dispute_outcome": {"outcome_code": "RESOLVED_BUYER_FAVOUR"}}}
    r = webhooks.handle({}, event)
    assert r == {"processed": True, "outcome": "dispute lost recorded"}
    assert seen == [("ORDER-1", False, "32.00", "PP-D-1")]
    assert webhooks.handle({}, event)["processed"] is False, "a repeated delivery changes nothing"


def test_a_seal_with_unchanged_facts_is_renewed_before_it_expires(client):
    import datetime, json
    cred = passport.issue("lydia")
    until = datetime.date.fromisoformat(cred["validUntil"][:10])
    assert passport.issue("lydia", today=until - datetime.timedelta(days=passport.RENEW_DAYS + 1))["id"] == cred["id"], "not due yet"
    renewed = passport.issue("lydia", today=until - datetime.timedelta(days=passport.RENEW_DAYS - 1))
    assert renewed["id"] != cred["id"] and renewed["validUntil"] > cred["validUntil"]
    assert renewed["credentialSubject"] == cred["credentialSubject"], "renewal changes the dates, never the facts"
    old = passport.status_of(cred["id"])
    assert old["status"] == "superseded" and "Renewed" in old["status_reason"]
    assert passport.verify(renewed)["result"] == "genuine"


def test_the_w3c_bitstring_status_list_marks_withdrawn_seals(client, admin):
    import base64, gzip
    cred = client.get("/api/merchants/lydia/seal").json()
    entry = next(s for s in cred["credentialStatus"] if s["type"] == "BitstringStatusListEntry")
    assert entry["statusPurpose"] == "revocation" and entry["statusListCredential"].endswith("/api/credentials/status-list/revocation")
    i = int(entry["statusListIndex"])

    def bit():
        lst = client.get("/api/credentials/status-list/revocation").json()
        assert "BitstringStatusListCredential" in lst["type"] and lst["proof"]["proofValue"]
        enc = lst["credentialSubject"]["encodedList"]
        raw = gzip.decompress(base64.urlsafe_b64decode(enc[1:] + "=" * (-len(enc[1:]) % 4)))
        assert len(raw) * 8 >= 131072
        return (raw[i // 8] >> (7 - i % 8)) & 1

    assert bit() == 0
    try:
        client.post("/api/admin/merchants/lydia/withdraw", json={"reason": REASON}, headers=admin)
        assert bit() == 1, "a withdrawn seal shows as revoked in the public list"
    finally:
        client.post("/api/admin/merchants/lydia/reinstate", json={"note": "Test finished."}, headers=admin)
