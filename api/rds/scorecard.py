"""The business view: one North Star and a balanced scorecard. Every number comes from the semantic layer
or a gold table, and every target is a project-set demo target, labelled as such."""
from __future__ import annotations

from . import warehouse as wh

HEADLINE_MODEL = "claude-sonnet-5-5"


def _model(m: str) -> str:
    name, *ver = m.replace("claude-", "").split("-")
    return f"{name.title()} {'.'.join(ver)}"


def _kpi(key, label, value, unit, target, good, note, source, display=None):
    return {"key": key, "label": label, "value": value, "unit": unit, "display": display or (f"{value}{unit}" if unit == "%" else str(value)),
            "target": target, "on_target": bool(good), "note": note, "source": source}


def build() -> dict:
    ag = {(r["model"], r["mode"]): r for r in wh.measure("agent_metrics", ["tasks", "small_shop_picks", "chain_picks", "fake_badge_picks", "small_shop_pct"], ["model", "mode"])}
    base, ver = ag[(HEADLINE_MODEL, "baseline")], ag[(HEADLINE_MODEL, "verified")]
    sw = {r["switch_type"]: r["n"] for r in wh.rows("SELECT switch_type, count(*) n FROM gold.fact_agent_switch WHERE model = ? GROUP BY 1", [HEADLINE_MODEL])}
    # PayPal value and shop standing count only businesses whose record was read back from PayPal. Shops with imported or
    # simulated records (the fictional demo shops, Bright Clean) appear on their passports, never in these totals.
    com = wh.measure("commerce_metrics", ["orders", "captured_usd", "net_usd", "refund_rate_pct", "average_order_usd", "tracking_rate_pct"],
                     where={"source_system": "paypal_sandbox_readback"})[0]
    tr = wh.measure("trust_metrics", ["shops", "sealed_shops", "rules_met", "rules_checked", "orders_behind_evidence"],
                    where={"evidence_basis": "paypal_record"})[0]
    ev = {r["evidence_class"]: r["n"] for r in wh.rows("SELECT evidence_class, count(*) n FROM gold.fact_metric_observations GROUP BY 1")}
    attacks = {r["model"]: r for r in wh.rows("SELECT model, count(*) FILTER (passed) passed, count(*) total FROM gold.fact_attack_run GROUP BY 1")}
    cat = wh.catalog()
    rules = [r for c in cat["contracts"] for r in c["rules"]]
    untracked = wh.one("""SELECT count(*) n FROM gold.fact_orders
                          WHERE in_recent_window AND is_fulfilled AND NOT has_tracking AND source_system = 'paypal_sandbox_readback'""")["n"]
    fake_total = sum(r["fake_badge_picks"] for r in ag.values())
    runs_total = sum(r["tasks"] for r in ag.values())
    confirmed = ev.get("paypal_sandbox_confirmed", 0)
    all_facts = sum(ev.values())
    return {
        "north_star": {
            "name": "Small-shop share of AI shopping decisions when evidence is available",
            "why": "It is the one number that moves only when the whole chain works: records are read, facts are signed, the agent reads them, and the shopper gets a better-grounded pick.",
            "value": ver["small_shop_pct"], "unit": "%", "numerator": ver["small_shop_picks"], "denominator": ver["tasks"],
            "baseline": base["small_shop_pct"], "baseline_numerator": base["small_shop_picks"],
            "lift_points": ver["small_shop_pct"] - base["small_shop_pct"], "model": HEADLINE_MODEL,
            "caveat": "A controlled test: 50 Home & Garden requests, one run each, one catalog. These are AI choices, not purchases or sales.",
            "by_model": [{"model": m, "baseline": ag[(m, "baseline")]["small_shop_pct"], "with_evidence": ag[(m, "verified")]["small_shop_pct"],
                          "baseline_n": ag[(m, "baseline")]["small_shop_picks"], "with_evidence_n": ag[(m, "verified")]["small_shop_picks"]}
                         for m in sorted({k[0] for k in ag})],
        },
        "perspectives": [
            {"key": "financial", "name": "Value for PayPal", "question": "Does evidence sit on real PayPal volume?", "kpis": [
                _kpi("net_usd", "Net PayPal sales behind the evidence", round(com["net_usd"]), "USD", "all captured volume covered", True,
                     f"{com['orders']} sandbox orders, ${round(com['captured_usd']):,} captured before refunds.", "commerce_metrics.net_usd", f"${round(com['net_usd']):,}"),
                _kpi("refund_rate", "Orders refunded", com["refund_rate_pct"], "%", "8% or lower", com["refund_rate_pct"] <= 8,
                     f"Across the {tr['shops']} shops with PayPal sandbox records, all history.", "commerce_metrics.refund_rate_pct"),
                _kpi("aov", "Average order", com["average_order_usd"], "USD", "context", True, "Captured amount per order.", "commerce_metrics.average_order_usd", f"${com['average_order_usd']:.2f}"),
            ]},
            {"key": "customer", "name": "Merchants and shoppers", "question": "Do honest shops get seen, and are shoppers protected?", "kpis": [
                _kpi("sealed", "Shops sealed", tr["sealed_shops"], "", f"of {tr['shops']} with PayPal records", True,
                     "One shop is not yet sealed and one is too new to judge. Both states are shown honestly.", "trust_metrics.sealed_shops", f"{tr['sealed_shops']} of {tr['shops']}"),
                _kpi("switches", "Decisions that moved chain to small shop", sw.get("chain_to_small", 0), "", "more than moved back", sw.get("chain_to_small", 0) > sw.get("small_to_chain", 0),
                     f"{sw.get('small_to_chain', 0)} moved the other way. Evidence informs; it does not force.", "gold.fact_agent_switch", f"{sw.get('chain_to_small', 0)} of 50"),
                _kpi("fake", "Picks of the shop with the forged badge", fake_total, "", "0", fake_total == 0,
                     f"Across {runs_total} recorded runs, two models, both conditions.", "agent_metrics.fake_badge_picks", f"{fake_total} of {runs_total}"),
            ]},
            {"key": "process", "name": "Evidence quality", "question": "Can every number be trusted and traced?", "kpis": [
                _kpi("contracts", "Data contract rules passing", len([r for r in rules if r["passed"]]), "", "all", all(r["passed"] for r in rules),
                     "Checked on every pipeline run. One failure stops the build.", "ops.contract_results", f"{len([r for r in rules if r['passed']])} of {len(rules)}"),
                _kpi("tracking", "Shipped orders with tracking", com["tracking_rate_pct"], "%", "90% or higher", com["tracking_rate_pct"] >= 90,
                     f"{untracked} recent shipped orders still have no tracking number. The coach lists them.", "commerce_metrics.tracking_rate_pct"),
                _kpi("confirmed", "Facts confirmed by PayPal sandbox records", round(100 * confirmed / all_facts), "%", "100% in production", False,
                     f"{confirmed} of {all_facts} published facts. The rest are merchant-reported or simulated, and labelled.", "gold.fact_metric_observations", f"{confirmed} of {all_facts}"),
            ]},
            {"key": "learning", "name": "Safety and learning", "question": "Does the agent hold up under attack, and are we improving?", "kpis": [
                *[_kpi(f"attacks_{m}", f"Attacks resisted ({_model(m)})", a["passed"], "", "all", a["passed"] == a["total"],
                       "Forged badges, hidden instructions, tampered seals, pressure.", "gold.fact_attack_run", f"{a['passed']} of {a['total']}") for m, a in sorted(attacks.items(), reverse=True)],
                _kpi("rules", "Published rules met across shops", tr["rules_met"], "", "context", True,
                     "Each unmet rule becomes a coach action for the shop.", "trust_metrics.rules_met", f"{tr['rules_met']} of {tr['rules_checked']}"),
            ]},
        ],
        "targets_note": "Targets are demonstration targets set by this project, not PayPal standards.",
        "pipeline_run": cat["run_id"],
    }
