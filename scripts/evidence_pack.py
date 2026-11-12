"""Build the judge evidence pack: run every test, then map each claim and each failure mode to the tests that prove it.

    python scripts/evidence_pack.py        (or: make evidence)

Writes docs/evidence/evidence-pack.json, docs/evidence/README.md, docs/evidence/test-report.txt, sdk/openapi.json
and sdk/postman_collection.json. A claim with no automated test is listed as 'Not automated', never as passing.
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "evidence"
PY = sys.executable

CLAIMS = [
    ("PayPal payment completed", ["test_real_mode_captures_only_what_paypal_confirms", "test_a_confirmed_paypal_order_joins_the_record_and_a_refund_recalculates_it", "test_a_capture_for_the_wrong_amount_is_refused"],
     "Proved against a stand-in for PayPal's Orders API. Not yet run against the live PayPal sandbox."),
    ("Source records were retrieved and reconcile", ["test_every_delivered_order_reaches_gold", "test_all_four_gates_pass", "test_rates_reconcile_with_version_one"], None),
    ("Merchant metric is correct", ["test_rates_reconcile_with_version_one", "test_net_sales_agree_from_orders_events_and_months", "test_passport_tool_gives_counts_and_evidence_class", "test_each_business_is_measured_only_on_metrics_for_its_type"], None),
    ("Credential cannot be silently edited", ["test_a_fresh_seal_is_genuine", "test_changing_one_number_breaks_the_seal", "test_changing_the_standing_breaks_the_seal", "test_verify_endpoint_spots_an_edit"], None),
    ("Merchant cannot access another tenant", ["test_one_business_cannot_read_another_businesss_evidence", "test_one_business_cannot_change_another_businesss_records", "test_a_business_cannot_add_tracking_to_someone_elses_order", "test_private_routes_need_a_session"], None),
    ("AI recommendation changed", ["test_headline_result_comes_from_the_semantic_layer", "test_scorecard_north_star_is_37_of_50_against_25"],
     "The tests prove the recorded traces are served unchanged. The runs themselves used the first version of the tools on 2026-11-10 and have not been repeated on this build."),
    ("Checkout cannot be duplicated", ["test_checkout_uses_the_server_price_and_is_idempotent", "test_a_session_is_captured_once_however_often_the_buyer_returns", "test_ten_simultaneous_returns_capture_once"], None),
    ("Merchant can improve a recorded metric", ["test_adding_tracking_raises_the_rate_and_is_recorded_before_and_after", "test_real_mode_tracking_is_sent_to_paypal"], None),
    ("API can be used by external developers", ["test_an_external_developer_can_search_read_and_verify", "test_mcp_lists_the_eight_tools", "test_mcp_tool_call_returns_the_passport", "test_the_openapi_contract_lists_the_public_and_private_routes"], None),
    ("Unsupported data is not falsely verified", ["test_imported_records_can_never_earn_the_seal", "test_simulated_history_is_always_labelled", "test_shops_without_a_paypal_record_get_no_standing", "test_a_simulated_checkout_never_becomes_evidence"], None),
    ("A new business joins without code changes", ["test_a_service_business_joins_and_is_judged_by_service_rules", "test_a_digital_business_is_judged_on_delivery_not_shipping", "test_an_operational_extract_adds_a_business_without_new_sql"], None),
    ("The shopper can choose the AI model (Gemini by default, Claude Opus or Sonnet)", ["test_health_lists_the_three_models_with_gemini_default", "test_model_resolution_and_fallback", "test_gemini_loop_follows_the_function_calling_protocol", "test_claude_opus_choice_reaches_anthropic_with_the_opus_model"], None),
    ("Real disputes reach the record", ["test_a_resolved_paypal_dispute_reaches_the_record"], None),
    ("Every product has an image, the same for every shop", ["test_every_product_has_an_image_and_every_shop_gets_the_same_treatment"], None),
    ("Statement totals reconcile and limits stay visible", ["test_statement_totals_reconcile_and_limits_stay_visible", "test_statement_is_shared_with_one_recipient_and_can_be_taken_back"], None),
]
ADVERSARIAL = [
    ("Copied trust badge", "No verification unless genuine credential data checks out", ["test_a_badge_or_a_sentence_is_not_a_seal", "test_a_shop_with_a_forged_badge_has_no_record_and_is_flagged"], None),
    ("Edited metric", "Signature or evidence validation fails", ["test_changing_one_number_breaks_the_seal"], None),
    ("Forged issuer", "Untrusted issuer is rejected", ["test_a_seal_signed_by_an_unknown_key_is_forged", "test_copying_our_key_id_onto_a_forged_seal_does_not_help"], None),
    ("Expired or withdrawn credential", "Not represented as currently valid", ["test_an_old_seal_expires", "test_a_withdrawn_seal_stops_verifying", "test_key_rotation_keeps_old_seals_valid_and_revocation_kills_them", "test_withdraw_for_cause_end_to_end"], None),
    ("Merchant text containing AI instructions", "Treated as untrusted data", ["test_seller_text_is_marked_untrusted_and_instructions_are_flagged", "test_seller_text_with_instructions_is_flagged"],
     "Code flags and wraps the text. The model ignoring it was recorded on 2026-11-10 and not re-run on this build."),
    ("Injected receipt instructions", "Ignored as commands", [], "The receipt reader from the first version is not part of this rebuild, so there is nothing to attack."),
    ("Wrong merchant ID in tool output", "No cross-merchant attribution", ["test_agent_tools_never_show_another_businesss_numbers", "test_a_business_cannot_add_tracking_to_someone_elses_order"], None),
    ("Simulated shipping history", "Clearly identified as simulated", ["test_simulated_history_is_always_labelled"], None),
    ("New merchant with limited history", "Insufficient-evidence state, not false negative judgment", ["test_a_new_shop_is_new_not_bad", "test_standings"], None),
    ("Missing transaction source", "No invented performance history", ["test_shops_without_a_paypal_record_get_no_standing", "test_an_unknown_shop_gets_an_honest_cannot_vouch", "test_an_empty_workspace_explains_what_is_missing"], None),
    ("Concurrent checkout attempts", "No duplicate financial effects", ["test_ten_simultaneous_returns_capture_once"], None),
    ("Stale catalog or stock", "Purchase blocked or reconfirmed", ["test_two_buyers_racing_for_the_last_unit_cannot_both_capture", "test_stock_runs_out"], None),
    ("Unauthorized data access", "Denied and recorded", ["test_one_business_cannot_read_another_businesss_evidence", "test_wrong_password_is_refused_and_audited"], None),
    ("Duplicate webhook", "Idempotent processing", ["test_webhook_is_processed_only_when_paypal_confirms_it_and_only_once"], None),
    ("Declined or canceled PayPal transaction", "No false successful-payment status", ["test_a_declined_capture_is_refused", "test_a_cancelled_checkout_is_never_captured", "test_a_denied_capture_webhook_never_shows_as_paid", "test_returning_without_approving_does_not_mark_paid"], None),
    ("Consent withdrawn", "New disclosures cease and credentials are updated appropriately", ["test_withdrawing_consent_revokes_the_passport_and_hides_the_record", "test_a_shop_that_takes_its_passport_down_is_shown_as_withdrawn_not_unknown"], None),
    ("A sealed shop turns out to be a scam", "Seal withdrawn for cause: check fails, shoppers and agents told why, no checkout, nobody else affected", ["test_withdrawing_needs_the_admin_token", "test_withdraw_for_cause_end_to_end"], None),
    ("Evidence switch leaks evidence into the baseline", "With evidence off, no standing, seal, hint or warning reaches the model or the page", ["test_search_with_evidence_off_carries_no_trust_information", "test_a_model_cannot_switch_the_baseline_off_or_on", "test_chat_api_evidence_off_offline_has_no_standing", "test_gemini_loop_follows_the_function_calling_protocol"], None),
    ("Model recommends an unsupported product", "Safe refusal or correction", ["test_no_checkout_for_a_shop_without_paypal"],
     "Code refuses the checkout. The model saying 'nothing fits' is graded by evals/tau task nothing-fits, which has not been run with a model."),
    ("Refund after credential issuance", "Dependent metrics become eligible for recalculation", ["test_a_confirmed_paypal_order_joins_the_record_and_a_refund_recalculates_it"], None),
]


def run_suite(path: Path) -> dict[str, dict]:
    xml = Path(tempfile.mkdtemp()) / "junit.xml"
    env = {**os.environ, "RDS_VAR_DIR": tempfile.mkdtemp(prefix="rds-evidence-")}
    for k in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        env.pop(k, None)
    env["RDS_NO_DOTENV"] = "1"
    r = subprocess.run([PY, "-m", "pytest", str(path), "-q", f"--junitxml={xml}"], cwd=REPO, env=env, capture_output=True, text=True)
    out = {}
    for case in ET.parse(xml).getroot().iter("testcase"):
        name = case.get("name").split("[")[0]
        ok = case.find("failure") is None and case.find("error") is None and case.find("skipped") is None
        prev = out.get(name, {"passed": True, "cases": 0})
        out[name] = {"passed": prev["passed"] and ok, "cases": prev["cases"] + 1, "file": case.get("classname").split(".")[-1]}
    return out, r.stdout.strip().splitlines()[-1]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tests, lines = {}, []
    for suite in ("data_platform/tests", "api/tests"):
        t, last = run_suite(REPO / suite)
        tests.update(t)
        lines.append(f"{suite}: {last}")
    oracle = subprocess.run([PY, "evals/tau/run.py", "--agent", "oracle", "--out", tempfile.mkdtemp()], cwd=REPO, capture_output=True, text=True).stdout.strip().splitlines()[-1]
    naive = subprocess.run([PY, "evals/tau/run.py", "--agent", "naive", "--out", tempfile.mkdtemp()], cwd=REPO, capture_output=True, text=True).stdout.strip().splitlines()[-1]
    lines += [f"evals/tau harness: {oracle}", f"evals/tau harness: {naive}"]

    def resolve(names):
        missing = [n for n in names if n not in tests]
        if missing:
            sys.exit(f"evidence map names tests that do not exist: {missing}")
        return [{"name": n, "file": tests[n]["file"], "passed": tests[n]["passed"]} for n in names]

    claims = [{"claim": c, "tests": resolve(t), "passed": bool(t) and all(tests[n]["passed"] for n in t), "note": note} for c, t, note in CLAIMS]
    adv = [{"case": c, "required": req, "tests": resolve(t), "passed": bool(t) and all(tests[n]["passed"] for n in t), "note": note} for c, req, t, note in ADVERSARIAL]
    total = sum(v["cases"] for v in tests.values())
    passed = sum(v["cases"] for v in tests.values() if v["passed"])
    pack = {"generated_at": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
            "summary": {"tests_total": total, "tests_passed": passed, "claims": len(claims), "claims_passing": sum(c["passed"] for c in claims),
                        "adversarial_cases": len(adv), "adversarial_passing": sum(a["passed"] for a in adv),
                        "adversarial_not_automated": sum(not a["tests"] for a in adv)},
            "runs": lines, "claims": claims, "adversarial": adv,
            "not_verified": ["Live PayPal sandbox calls (checkout, tracking, refund, webhook verification) are exercised against a stand-in for PayPal's API.",
                             "The assistant has not been run with a live model on this build; the 50-task result is the recorded run of 2026-11-10.",
                             "promptfoo and ArkSim configurations are written but have not been run.",
                             "The container image and Render deployment have not been built or deployed."]}
    (OUT / "evidence-pack.json").write_text(json.dumps(pack, indent=1))
    (OUT / "test-report.txt").write_text("\n".join(lines) + "\n")
    mark = lambda x: "Passing" if x["passed"] else ("FAILING" if x["tests"] else "Not automated")  # noqa: E731
    md = [f"# Evidence pack\n\nGenerated {pack['generated_at']} by `scripts/evidence_pack.py`. {passed} of {total} automated tests passed.\n",
          "## Claims\n\n| Claim | Tests | Result | Note |\n|---|---|---|---|"]
    md += [f"| {c['claim']} | {', '.join('`' + t['name'] + '`' for t in c['tests'])} | {mark(c)} | {c['note'] or ''} |" for c in claims]
    md += ["\n## Attacks and failure modes\n\n| Case | Required behaviour | Tests | Result | Note |\n|---|---|---|---|---|"]
    md += [f"| {a['case']} | {a['required']} | {', '.join('`' + t['name'] + '`' for t in a['tests']) or 'none'} | {mark(a)} | {a['note'] or ''} |" for a in adv]
    md += ["\n## Not verified\n"] + [f"- {n}" for n in pack["not_verified"]] + ["\n## Runs\n"] + [f"- {l}" for l in lines]
    (OUT / "README.md").write_text("\n".join(md) + "\n")

    # Published API contract and a Postman collection generated from it.
    os.environ["RDS_VAR_DIR"] = tempfile.mkdtemp(prefix="rds-openapi-")
    sys.path.insert(0, str(REPO / "api"))
    from rds.main import app
    spec = app.openapi()
    (REPO / "sdk" / "openapi.json").write_text(json.dumps(spec, indent=1))
    items = []
    for path, ops in sorted(spec["paths"].items()):
        for method, op in ops.items():
            items.append({"name": op.get("summary", path), "request": {
                "method": method.upper(), "header": [{"key": "Authorization", "value": "Bearer {{token}}"}] if "/studio/" in path else [],
                "url": {"raw": "{{baseUrl}}" + path.replace("{", ":").replace("}", ""), "host": ["{{baseUrl}}"], "path": [s.replace("{", ":").replace("}", "") for s in path.strip("/").split("/")]},
                **({"body": {"mode": "raw", "raw": "{}", "options": {"raw": {"language": "json"}}}} if method in ("post", "put") else {})}})
    (REPO / "sdk" / "postman_collection.json").write_text(json.dumps({
        "info": {"name": "Real Deal Seal API", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
        "variable": [{"key": "baseUrl", "value": "http://localhost:8000"}, {"key": "token", "value": ""}], "item": items}, indent=1))
    print("\n".join(lines))
    print(f"claims passing {pack['summary']['claims_passing']}/{len(claims)}; attack cases passing {pack['summary']['adversarial_passing']}/{len(adv)} ({pack['summary']['adversarial_not_automated']} not automated)")


if __name__ == "__main__":
    main()
