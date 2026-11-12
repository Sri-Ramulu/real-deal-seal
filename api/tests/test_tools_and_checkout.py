import pytest

from rds import checkout, config, refresh, store, tools


def test_search_is_ordered_by_relevance_then_price_never_trust():
    offers = tools.search_products("purple table runner")["offers"]
    assert offers[0]["shop_id"] == "babel"  # cheapest equally relevant offer comes first, sealed or not
    assert {"lydia", "palace"} <= {o["shop_id"] for o in offers}


def test_seller_text_is_marked_untrusted_and_instructions_are_flagged():
    palace = next(o for o in tools.search_products("purple table runner")["offers"] if o["shop_id"] == "palace")
    assert palace["seller_text"]["untrusted"] and palace["shop_self_claim"]["contains_instructions_for_ai"]


def test_passport_tool_gives_counts_and_evidence_class():
    p = tools.get_merchant_passport("lydia")
    tracking = next(f for f in p["facts"] if f["fact"] == "Shipped orders with tracking")
    assert tracking == {"fact": "Shipped orders with tracking", "value": "96%", "counted": "47 of 49",
                        "window": "last 50 completed orders", "evidence": "merchant_reported"}
    assert p["seal_check"] == "genuine"


def test_a_new_shop_is_new_not_bad():
    p = tools.get_merchant_passport("priscilla")
    assert p["standing"] == "Not enough history yet" and "too short to judge" in p["verdict"]


def test_an_unknown_shop_gets_an_honest_cannot_vouch():
    r = tools.check_any_shop("https://www.totally-new-shop.com/store")
    assert r["found"] is False and "either way" in r["message"]


def test_check_any_shop_finds_a_known_shop_by_name():
    assert tools.check_any_shop("Lydia Linen Co.")["standing"] == "Real Deal: sealed"


def test_a_shop_with_a_forged_badge_has_no_record_and_is_flagged():
    r = tools.get_merchant_passport("palace")
    assert r["standing"] == "No PayPal record on file" and r["displays_badge_that_does_not_verify"]


def test_sealed_alternative_is_the_same_kind_of_item_or_nothing():
    r = tools.find_sealed_alternative("BH-RUN-01")
    assert r["found"] and all(a["shop_id"] == "lydia" and "runner" in a["product"].lower() for a in r["alternatives"])


def test_market_prices_are_labelled_as_context_only():
    r = tools.compare_market_prices("purple linen table runner")
    assert r["available"] and "None has a PayPal record" in r["note"]


def test_bad_tool_arguments_return_a_helpful_error():
    assert "Bad arguments" in tools.call("search_products", {"nope": 1})["error"]


def test_checkout_uses_the_server_price_and_is_idempotent():
    a = checkout.create("JF-NAP-LV", 2, idempotency_key="k-1")
    b = checkout.create("JF-NAP-LV", 2, idempotency_key="k-1")
    assert a["session_id"] == b["session_id"] and a["amount_usd"] == "56.00" and a["mode"] == "simulated"


def test_a_session_is_captured_once_however_often_the_buyer_returns():
    s = checkout.create("JF-RUN-IT", 1)
    first, second = checkout.complete(s["paypal_order_id"]), checkout.complete(s["paypal_order_id"])
    assert first["status"] == second["status"] == "CAPTURED" and first["capture_id"] == second["capture_id"]
    assert len([e for e in store.recent_audit(200) if e["action"] == "checkout.capture" and e["target"] == s["session_id"]]) == 1


def test_no_checkout_for_a_shop_without_paypal():
    with pytest.raises(checkout.CheckoutError) as e:
        checkout.create("BH-RUN-01")
    assert e.value.code == "no_paypal_checkout"


def test_stock_runs_out():
    sku = "JF-CUR-HT"
    left = checkout.available_stock(sku)
    for _ in range(left // 10):
        checkout.complete(checkout.create(sku, 10)["paypal_order_id"])
    rest = checkout.available_stock(sku)
    if rest:
        checkout.complete(checkout.create(sku, rest)["paypal_order_id"])
    with pytest.raises(checkout.CheckoutError) as e:
        checkout.create(sku, 1)
    assert e.value.code == "out_of_stock"


def test_a_cancelled_checkout_is_never_captured():
    s = checkout.create("JF-RUN-PD", 1)
    assert checkout.cancel(s["paypal_order_id"])["status"] == "CANCELLED"
    assert checkout.complete(s["paypal_order_id"])["status"] == "CANCELLED"


@pytest.fixture()
def fake_paypal(monkeypatch):
    """Stand-in for PayPal's Orders API so the real-mode code path runs without the network."""
    state = {"calls": [], "order_status": "APPROVED", "capture_status": "COMPLETED", "capture_value": None}

    def api(merchant_id, method, path, request_id=None, body=None):
        state["calls"].append((method, path, request_id))
        if method == "POST" and path == "/v2/checkout/orders":
            state["amount"] = body["purchase_units"][0]["amount"]["value"]
            return {"id": "PP-" + request_id[:8], "status": "PAYER_ACTION_REQUIRED",
                    "links": [{"rel": "payer-action", "href": "https://www.sandbox.paypal.com/checkoutnow?token=PP"}]}
        if method == "GET":
            return {"id": path.rsplit("/", 1)[1], "status": state["order_status"], "purchase_units": [{}]}
        return {"status": "COMPLETED", "purchase_units": [{"payments": {"captures": [
            {"id": "CAP123", "status": state["capture_status"], "amount": {"value": state["capture_value"] or state["amount"], "currency_code": "USD"}}]}}]}

    monkeypatch.setattr(config, "paypal_credentials", lambda m: ("id", "secret"))
    monkeypatch.setattr(refresh, "run", lambda reason="": state.setdefault("refreshes", []).append(reason) or {"ok": True})
    monkeypatch.setattr(checkout, "_paypal", api)
    return state


def test_real_mode_captures_only_what_paypal_confirms(fake_paypal):
    s = checkout.create("JF-RUN-PD", 1)
    assert s["mode"] == "paypal_sandbox" and s["approve_url"].startswith("https://www.sandbox.paypal.com")
    done = checkout.complete(s["paypal_order_id"])
    assert done["status"] == "CAPTURED" and done["capture_id"] == "CAP123"
    assert [c[0] for c in fake_paypal["calls"]] == ["POST", "GET", "POST"]
    assert fake_paypal["refreshes"] == ["checkout.capture"]  # the confirmed order is sent to the evidence pipeline


def test_returning_without_approving_does_not_mark_paid(fake_paypal):
    fake_paypal["order_status"] = "PAYER_ACTION_REQUIRED"
    s = checkout.create("JF-RUN-PD", 1)
    with pytest.raises(checkout.CheckoutError) as e:
        checkout.complete(s["paypal_order_id"])
    assert e.value.code == "not_approved" and store.session(s["session_id"])["status"] == "CREATED"


def test_a_capture_for_the_wrong_amount_is_refused(fake_paypal):
    fake_paypal["capture_value"] = "1.00"
    s = checkout.create("JF-RUN-PD", 1)
    with pytest.raises(checkout.CheckoutError) as e:
        checkout.complete(s["paypal_order_id"])
    assert e.value.code == "capture_not_completed" and store.session(s["session_id"])["status"] == "FAILED"


def test_a_declined_capture_is_refused(fake_paypal):
    fake_paypal["capture_status"] = "DECLINED"
    s = checkout.create("JF-RUN-PD", 1)
    with pytest.raises(checkout.CheckoutError):
        checkout.complete(s["paypal_order_id"])
    assert store.session(s["session_id"])["status"] == "FAILED"
