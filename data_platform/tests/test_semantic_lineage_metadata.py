import pytest

from rdsp import lineage, semantic


def test_measure_compiles_to_one_definition():
    sql, params = semantic.compile_query("agent_metrics", ["small_shop_pct"], ["mode"], {"model": "claude-sonnet-5-5"})
    assert "FROM gold.fact_agent_choice" in sql and "GROUP BY 1" in sql and params == ["claude-sonnet-5-5"]


def test_unknown_measure_is_refused():
    with pytest.raises(KeyError, match="do not hand-write"):
        semantic.compile_query("commerce_metrics", ["revenue_but_my_way"])


def test_headline_result_comes_from_the_semantic_layer(con):
    rows = semantic.query(con, "agent_metrics", ["small_shop_picks", "tasks"], ["mode"], {"model": "claude-sonnet-5-5"})
    assert rows == [{"mode": "baseline", "small_shop_picks": 25, "tasks": 50}, {"mode": "verified", "small_shop_picks": 37, "tasks": 50}]


def test_net_sales_agree_between_semantic_layer_and_passport(con):
    by_shop = {r["merchant_id"]: round(r["net_usd"]) for r in semantic.query(con, "commerce_metrics", ["net_usd"], ["merchant_id"])}
    passport = dict(con.execute("SELECT merchant_id, net_sales_usd FROM gold.merchant_passport WHERE has_paypal_record").fetchall())
    assert by_shop == passport


def test_every_model_declares_what_it_reads_and_writes():
    for m in lineage.models():
        assert m["writes"].split(".")[0] == m["layer"], m["file"]
        assert m["reads"], m["file"]
        assert not [r for r in m["reads"] if m["layer"] == "gold" and r.startswith("bronze.")], f"{m['file']} reads bronze from gold"


def test_passport_traces_back_to_the_paypal_files(catalog):
    up = lineage.upstream(catalog["lineage"], "gold.merchant_passport")
    assert "landing/paypal/lydia.orders.json" in up and "landing/reference/criteria.json" in up
    assert "bronze.agent_eval_results" not in up


def test_every_gold_table_has_an_owner_and_a_description(catalog):
    gold = [t for t in catalog["tables"] if t["layer"] == "gold"]
    assert gold and not [t["name"] for t in gold if not t["description"] or not t["owner"]]


@pytest.mark.parametrize("table", ["gold.merchant_passport", "gold.agent_offers", "gold.fact_metric_observations", "gold.fact_orders"])
def test_agent_facing_tables_document_every_column(catalog, table):
    t = next(t for t in catalog["tables"] if t["name"] == table)
    assert not [c["name"] for c in t["columns"] if not c.get("meaning")]


def test_every_product_has_a_contract(catalog):
    assert {p["id"] for p in catalog["products"]} == {c["domain"] + "." + {"merchant": "directory", "commerce": "record", "trust": "passport", "agent": "decisions"}[c["domain"]] for c in catalog["contracts"]}
