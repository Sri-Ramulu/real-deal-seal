"""The gold layer is a star: conformed dimensions with unique surrogate keys, facts at a declared grain that
point at them, and totals that agree whichever fact you start from."""
import pytest

DIMS = {"gold.dim_merchant": "merchant_key", "gold.dim_date": "date_key", "gold.dim_product": "product_key", "gold.dim_source_system": "source_system_key",
        "gold.dim_metric": "metric_key", "gold.dim_rule": "rule_key", "gold.dim_evidence_class": "evidence_class_key", "gold.dim_model": "model_key"}
FKS = [("gold.fact_orders", "merchant_key", "gold.dim_merchant", "merchant_key"), ("gold.fact_orders", "order_date_key", "gold.dim_date", "date_key"),
       ("gold.fact_orders", "source_system_key", "gold.dim_source_system", "source_system_key"),
       ("gold.fact_payment_events", "merchant_key", "gold.dim_merchant", "merchant_key"), ("gold.fact_payment_events", "event_date_key", "gold.dim_date", "date_key"),
       ("gold.fact_fulfillment_events", "merchant_key", "gold.dim_merchant", "merchant_key"), ("gold.fact_monthly_sales", "merchant_key", "gold.dim_merchant", "merchant_key"),
       ("gold.fact_metric_observations", "merchant_key", "gold.dim_merchant", "merchant_key"), ("gold.fact_metric_observations", "metric_key", "gold.dim_metric", "metric_key"),
       ("gold.fact_metric_observations", "evidence_class_key", "gold.dim_evidence_class", "evidence_class_key"),
       ("gold.fact_rule_results", "merchant_key", "gold.dim_merchant", "merchant_key"), ("gold.fact_rule_results", "rule_key", "gold.dim_rule", "rule_key"),
       ("gold.dim_product", "merchant_key", "gold.dim_merchant", "merchant_key"), ("gold.dim_rule", "metric_key", "gold.dim_metric", "metric_key"),
       ("gold.fact_agent_choice", "model_key", "gold.dim_model", "model_key"), ("gold.agent_offers", "product_key", "gold.dim_product", "product_key")]


@pytest.mark.parametrize("dim,key", DIMS.items())
def test_dimension_keys_are_unique_and_never_null(con, dim, key):
    total, distinct, nulls = con.execute(f"SELECT count(*), count(DISTINCT {key}), count(*) FILTER ({key} IS NULL) FROM {dim}").fetchone()
    assert total == distinct > 0 and nulls == 0


@pytest.mark.parametrize("fact,fk,dim,pk", FKS)
def test_every_foreign_key_finds_its_dimension_row(con, fact, fk, dim, pk):
    orphans = con.execute(f"SELECT count(*) FROM {fact} f WHERE f.{fk} IS NOT NULL AND NOT EXISTS (SELECT 1 FROM {dim} d WHERE d.{pk} = f.{fk})").fetchone()[0]
    assert orphans == 0


def test_the_merchant_dimension_is_conformed_across_domains(catalog):
    edges = [e for e in catalog["lineage"]["edges"] if e["from"] == "gold.dim_merchant"]
    domains = {next(n["domain"] for n in catalog["lineage"]["nodes"] if n["id"] == e["to"]) for e in edges}
    assert {"commerce", "trust"} <= domains


def test_net_sales_agree_from_orders_events_and_months(con):
    a = con.execute("SELECT sum(net_usd) FROM gold.fact_orders").fetchone()[0]
    b = con.execute("SELECT sum(signed_amount_usd) FROM gold.fact_payment_events").fetchone()[0]
    c = con.execute("SELECT sum(net_usd) FROM gold.fact_monthly_sales").fetchone()[0]
    assert a == b == c


def test_a_star_query_answers_a_business_question_in_one_join_per_dimension(con):
    rows = con.execute("""SELECT m.merchant_name, d.year_month, s.source_system, count(*) orders, sum(f.net_usd) net
                          FROM gold.fact_orders f JOIN gold.dim_merchant m USING (merchant_key)
                          JOIN gold.dim_date d ON d.date_key = f.order_date_key JOIN gold.dim_source_system s USING (source_system_key)
                          WHERE m.merchant_id = 'lydia' GROUP BY ALL ORDER BY 2""").fetchall()
    assert sum(r[3] for r in rows) == 100 and {r[2] for r in rows} == {"paypal_sandbox_readback"}


def test_each_business_is_measured_only_on_metrics_for_its_type(con):
    got = {r[0] for r in con.execute("SELECT metric FROM gold.fact_metric_observations WHERE merchant_id = 'lydia'").fetchall()}
    assert {"tracking_rate", "fast_ship_rate"} <= got and not {"completion_rate", "delivery_rate", "cancellation_rate"} & got


def test_metric_definitions_cover_three_layers(con):
    assert [r[0][0] for r in con.execute("SELECT DISTINCT layer FROM gold.dim_metric ORDER BY 1").fetchall()] == ["A", "B", "C"]


def test_every_gold_column_is_documented(catalog):
    gaps = [f"{t['name']}.{c['name']}" for t in catalog["tables"] if t["layer"] == "gold" for c in t["columns"] if not c.get("meaning")]
    assert gaps == []


def test_an_operational_extract_adds_a_business_without_new_sql(tmp_path, monkeypatch):
    """A business that exists only in the operational extract flows through the same models as the demo shops."""
    import json
    import duckdb
    from rdsp import runner
    ops = tmp_path / "extract" / "ops"
    ops.mkdir(parents=True)
    (ops / "merchants.jsonl").write_text(json.dumps({"merchant_id": "studio-x", "origin": "workspace", "name": "Studio X", "business_type": "digital", "category": "Digital",
                                                     "region": "US", "passport_published": True, "hidden_metrics": [], "connection_provider": "records_import", "connection_status": "active"}) + "\n")
    orders, pay, ful = [], [], []
    for i in range(1, 41):
        oid = f"studio-x:{i}"
        orders.append({"order_id": oid, "merchant_id": "studio-x", "seq": i, "order_date": f"2026-{8 if i <= 20 else 10:02d}-{1 + i % 27:02d}", "amount_usd": "20.00", "status": "COMPLETED",
                       "source_system": "merchant_import", "payer_key": f"k{i % 9}", "item_count": 1, "simulated": False, "recorded_at": "2026-11-01T00:00:00"})
        pay.append({"event_id": f"cap:{oid}", "order_id": oid, "merchant_id": "studio-x", "event_type": "capture", "amount_usd": "20.00", "event_date": orders[-1]["order_date"], "evidence_class": "merchant_reported"})
        ful.append({"event_id": f"ful:{oid}", "order_id": oid, "merchant_id": "studio-x", "event_type": "digital_delivered", "days_after_payment": 0, "evidence_class": "merchant_reported"})
    for name, rows in (("orders", orders), ("payment_events", pay), ("fulfillment_events", ful)):
        (ops / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    monkeypatch.setenv("RDS_EXTRACT_DIR", str(tmp_path / "extract"))
    runner.build(tmp_path / "w.duckdb", quiet=True, catalog_out=tmp_path / "c.json")
    c = duckdb.connect(str(tmp_path / "w.duckdb"), read_only=True)
    assert c.execute("SELECT standing, evidence_basis, ruleset, rules_met, rules_total, delivery_pct FROM gold.merchant_passport WHERE merchant_id = 'studio-x'").fetchone() == \
        ("reported", "merchant_import", "digital", 4, 4, 100)
    assert c.execute("SELECT count(*) FROM gold.fact_orders").fetchone()[0] == 215
