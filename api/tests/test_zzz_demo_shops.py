"""The four fictional shops that join at startup (api/rds/demo_shops.py), and what the Evidence switch shows of them.

Runs last: it adds businesses to the shared test store.
"""
import json

import pytest

from rds import agent, demo_shops, tools, warehouse

SCAMS = ["violet-vine-home", "juniper-oak-goods"]


@pytest.fixture(scope="module")
def shops(client):
    created = demo_shops.ensure()
    return created


def test_the_four_shops_join_once(shops):
    assert sorted(shops) == sorted(SCAMS + ["copper-kettle-supply", "sage-stone-studio"])
    assert demo_shops.ensure() == [], "a restart must not create anything twice"


def test_convincing_scams_are_withdrawn_with_a_reason_from_their_record(shops):
    for mid in SCAMS:
        p = warehouse.one("SELECT standing, headline, verdict, seal_withdrawn_by FROM gold.merchant_passport WHERE merchant_id = ?", [mid])
        assert p["standing"] == "withdrawn" and p["seal_withdrawn_by"] == "issuer" and p["headline"] == "Seal withdrawn"
        assert "simulated demo records" in p["verdict"] and "disputes the shop lost" in p["verdict"]


def test_the_weak_shop_and_the_new_shop_are_not_withdrawn(shops):
    weak = warehouse.one("SELECT standing, rules_met, rules_total FROM gold.merchant_passport WHERE merchant_id = 'copper-kettle-supply'")
    assert weak["standing"] == "reported" and weak["rules_met"] < weak["rules_total"]
    new = warehouse.one("SELECT standing FROM gold.merchant_passport WHERE merchant_id = 'sage-stone-studio'")
    assert new["standing"] == "new"


def test_their_records_are_labelled_reported_or_simulated_never_paypal_confirmed(shops):
    rows = warehouse.rows("SELECT DISTINCT evidence_class FROM gold.fact_payment_events WHERE merchant_id IN ('violet-vine-home','juniper-oak-goods','copper-kettle-supply','sage-stone-studio')")
    assert {r["evidence_class"] for r in rows} <= {"merchant_reported", "simulated"}


def test_scam_listings_look_clean_and_cheaper_than_the_sealed_shop(shops):
    off = tools.search_products("purple table runner", evidence=False)["offers"]
    vv = next(o for o in off if o["shop_id"] == "violet-vine-home")
    lydia = next(o for o in off if o["shop_id"] == "lydia")
    assert vv["price_usd"] < lydia["price_usd"]
    assert vv["ships_from"] and vv["returns"] and "ignore" not in vv["seller_text"]["text"].lower()


def test_evidence_off_does_not_leak_a_withdrawal(shops):
    off = tools.search_products("purple table runner", evidence=False)
    vv = next(o for o in off["offers"] if o["shop_id"] == "violet-vine-home")
    assert vv["paypal_checkout"] is True, "the listing fact (takes PayPal) must not reveal the withdrawal"
    text = json.dumps(off).lower()
    for word in ("withdrawn", "withdrew", "seal", "standing", "dispute"):
        assert word not in text, word
    refused = tools.call("create_checkout", {"sku": "VV-RUN-PD"}, evidence=False)
    assert refused["created"] is False and "seal" not in json.dumps(refused).lower()


def test_evidence_on_shows_the_withdrawal_and_refuses_checkout(shops):
    on = tools.search_products("purple table runner")["offers"]
    vv = next(o for o in on if o["shop_id"] == "violet-vine-home")
    assert vv["shop_standing"] == "Seal withdrawn" and vv["paypal_checkout"] is False
    passport = tools.get_merchant_passport("violet-vine-home")
    assert passport.get("do_not_recommend") is True
    assert tools.call("create_checkout", {"sku": "VV-RUN-PD"})["reason"] == "seal_withdrawn"


def test_every_new_product_has_its_own_picture(client, shops):
    from rds import product_art
    for p in warehouse.rows("""SELECT sku, product_name, tags FROM gold.dim_product JOIN gold.dim_merchant USING (merchant_id)
                               WHERE business_type = 'physical'"""):
        kind, _, _ = product_art.classify(p["product_name"], p["tags"])
        words = dict(product_art.TYPES)[kind]
        assert any(w in (p["product_name"] + " " + " ".join(p["tags"])).lower() for w in words), (p["sku"], kind)
        assert client.get(f"/api/products/{p['sku']}/image.svg").status_code == 200


def test_offline_assistant_still_answers_with_the_new_shops(client, shops):
    r = agent.chat([{"role": "user", "content": "lavender napkins"}], evidence=False)
    assert r["offers"]
