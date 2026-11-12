"""The build is green, and gold reconciles with the source and with the figures of the first version."""
import json

import duckdb
import pytest

from rdsp import LANDING, contracts


def test_all_four_gates_pass(catalog):
    assert [g["gate"] for g in catalog["gates"]] == [1, 2, 3, 4]
    assert all(g["failed"] == 0 for g in catalog["gates"])


def test_every_delivered_order_reaches_gold(con):
    delivered = sum(len(json.loads(f.read_text())["orders"]) for f in (LANDING / "paypal").glob("*.orders.json"))
    assert con.execute("SELECT count(*) FROM gold.fact_orders").fetchone()[0] == delivered == 175


@pytest.mark.parametrize("shop,standing", [("lydia", "sealed"), ("martha", "verified"), ("priscilla", "new")])
def test_standings(con, shop, standing):
    assert con.execute("SELECT standing FROM gold.merchant_passport WHERE merchant_id = ?", [shop]).fetchone()[0] == standing


@pytest.mark.parametrize("shop", ["lydia", "martha", "priscilla"])
def test_rates_reconcile_with_version_one(con, shop):
    """The first version computed these in Python from the same PayPal read-back. SQL must agree."""
    v1 = {f["key"]: f["value"] for f in json.loads((LANDING / "reference" / f"v1_facts_{shop}.json").read_text())["facts"]}
    got = dict(con.execute("SELECT metric, value FROM gold.fact_metric_observations WHERE merchant_id = ?", [shop]).fetchall())
    for metric in ("orders_completed", "tracking_rate", "fast_ship_rate", "refund_rate", "disputes_total", "repeat_buyer_rate"):
        assert got[metric] == v1[metric], metric
    assert got["sales_net_usd"] == int(v1["sales_net_usd"].replace(",", ""))


def test_shops_without_a_paypal_record_get_no_standing(con):
    rows = con.execute("SELECT standing, orders_completed FROM gold.merchant_passport WHERE merchant_id IN ('babel','palace')").fetchall()
    assert rows == [("no_record", None), ("no_record", None)]


def test_seller_text_with_instructions_is_flagged(con):
    assert con.execute("SELECT seller_text_has_instructions, shows_unverifiable_badge FROM gold.merchant_passport WHERE merchant_id = 'palace'").fetchone() == (True, True)
    assert con.execute("SELECT count(*) FROM gold.merchant_passport WHERE seller_text_has_instructions AND merchant_id <> 'palace'").fetchone()[0] == 0


def test_no_buyer_names_or_emails_in_silver_or_gold(con):
    cols = [r[0].lower() for r in con.execute("SELECT column_name FROM information_schema.columns WHERE table_schema IN ('silver','gold')").fetchall()]
    assert not [c for c in cols if any(w in c for w in ("email", "buyer_name", "address", "phone"))]


def test_a_broken_promise_turns_the_contract_red(built, tmp_path):
    import shutil
    copy = tmp_path / "broken.duckdb"
    shutil.copy(built[0], copy)
    c = duckdb.connect(str(copy))
    c.execute("UPDATE gold.merchant_passport SET standing = 'sealed' WHERE merchant_id = 'martha'")
    failed = [r for r in contracts.check(c) if not r["passed"]]
    c.close()
    assert [r["rule"] for r in failed] == ["a sealed business meets every rule"]
