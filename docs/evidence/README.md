# Evidence pack

Generated 2026-11-12T09:16:38+00:00 by `scripts/evidence_pack.py`. 163 of 165 automated tests passed.

## Claims

| Claim | Tests | Result | Note |
|---|---|---|---|
| PayPal payment completed | `test_real_mode_captures_only_what_paypal_confirms`, `test_a_confirmed_paypal_order_joins_the_record_and_a_refund_recalculates_it`, `test_a_capture_for_the_wrong_amount_is_refused` | Passing | Proved against a stand-in for PayPal's Orders API. Not yet run against the live PayPal sandbox. |
| Source records were retrieved and reconcile | `test_every_delivered_order_reaches_gold`, `test_all_four_gates_pass`, `test_rates_reconcile_with_version_one` | Passing |  |
| Merchant metric is correct | `test_rates_reconcile_with_version_one`, `test_net_sales_agree_from_orders_events_and_months`, `test_passport_tool_gives_counts_and_evidence_class`, `test_each_business_is_measured_only_on_metrics_for_its_type` | Passing |  |
| Credential cannot be silently edited | `test_a_fresh_seal_is_genuine`, `test_changing_one_number_breaks_the_seal`, `test_changing_the_standing_breaks_the_seal`, `test_verify_endpoint_spots_an_edit` | Passing |  |
| Merchant cannot access another tenant | `test_one_business_cannot_read_another_businesss_evidence`, `test_one_business_cannot_change_another_businesss_records`, `test_a_business_cannot_add_tracking_to_someone_elses_order`, `test_private_routes_need_a_session` | Passing |  |
| AI recommendation changed | `test_headline_result_comes_from_the_semantic_layer`, `test_scorecard_north_star_is_37_of_50_against_25` | Passing | The tests prove the recorded traces are served unchanged. The runs themselves used the first version of the tools on 2026-11-10 and have not been repeated on this build. |
| Checkout cannot be duplicated | `test_checkout_uses_the_server_price_and_is_idempotent`, `test_a_session_is_captured_once_however_often_the_buyer_returns`, `test_ten_simultaneous_returns_capture_once` | Passing |  |
| Merchant can improve a recorded metric | `test_adding_tracking_raises_the_rate_and_is_recorded_before_and_after`, `test_real_mode_tracking_is_sent_to_paypal` | Passing |  |
| API can be used by external developers | `test_an_external_developer_can_search_read_and_verify`, `test_mcp_lists_the_eight_tools`, `test_mcp_tool_call_returns_the_passport`, `test_the_openapi_contract_lists_the_public_and_private_routes` | Passing |  |
| Unsupported data is not falsely verified | `test_imported_records_can_never_earn_the_seal`, `test_simulated_history_is_always_labelled`, `test_shops_without_a_paypal_record_get_no_standing`, `test_a_simulated_checkout_never_becomes_evidence` | Passing |  |
| A new business joins without code changes | `test_a_service_business_joins_and_is_judged_by_service_rules`, `test_a_digital_business_is_judged_on_delivery_not_shipping`, `test_an_operational_extract_adds_a_business_without_new_sql` | Passing |  |
| The shopper can choose the AI model (Gemini by default, Claude Sonnet or Haiku) | `test_health_lists_the_three_models_with_gemini_default`, `test_model_resolution_and_fallback`, `test_gemini_loop_follows_the_function_calling_protocol`, `test_claude_haiku_choice_reaches_anthropic_with_the_haiku_model` | Passing |  |
| Real disputes reach the record | `test_a_resolved_paypal_dispute_reaches_the_record` | Passing |  |
| Every product has an image, the same for every shop | `test_every_product_has_an_image_and_every_shop_gets_the_same_treatment` | Passing |  |
| Statement totals reconcile and limits stay visible | `test_statement_totals_reconcile_and_limits_stay_visible`, `test_statement_is_shared_with_one_recipient_and_can_be_taken_back` | Passing |  |

## Attacks and failure modes

| Case | Required behaviour | Tests | Result | Note |
|---|---|---|---|---|
| Copied trust badge | No verification unless genuine credential data checks out | `test_a_badge_or_a_sentence_is_not_a_seal`, `test_a_shop_with_a_forged_badge_has_no_record_and_is_flagged` | Passing |  |
| Edited metric | Signature or evidence validation fails | `test_changing_one_number_breaks_the_seal` | Passing |  |
| Forged issuer | Untrusted issuer is rejected | `test_a_seal_signed_by_an_unknown_key_is_forged`, `test_copying_our_key_id_onto_a_forged_seal_does_not_help` | Passing |  |
| Expired or withdrawn credential | Not represented as currently valid | `test_an_old_seal_expires`, `test_a_withdrawn_seal_stops_verifying`, `test_key_rotation_keeps_old_seals_valid_and_revocation_kills_them`, `test_withdraw_for_cause_end_to_end` | Passing |  |
| Merchant text containing AI instructions | Treated as untrusted data | `test_seller_text_is_marked_untrusted_and_instructions_are_flagged`, `test_seller_text_with_instructions_is_flagged` | Passing | Code flags and wraps the text. The model ignoring it was recorded on 2026-11-10 and not re-run on this build. |
| Injected receipt instructions | Ignored as commands | none | Not automated | The receipt reader from the first version is not part of this rebuild, so there is nothing to attack. |
| Wrong merchant ID in tool output | No cross-merchant attribution | `test_agent_tools_never_show_another_businesss_numbers`, `test_a_business_cannot_add_tracking_to_someone_elses_order` | Passing |  |
| Simulated shipping history | Clearly identified as simulated | `test_simulated_history_is_always_labelled` | Passing |  |
| New merchant with limited history | Insufficient-evidence state, not false negative judgment | `test_a_new_shop_is_new_not_bad`, `test_standings` | Passing |  |
| Missing transaction source | No invented performance history | `test_shops_without_a_paypal_record_get_no_standing`, `test_an_unknown_shop_gets_an_honest_cannot_vouch`, `test_an_empty_workspace_explains_what_is_missing` | Passing |  |
| Concurrent checkout attempts | No duplicate financial effects | `test_ten_simultaneous_returns_capture_once` | Passing |  |
| Stale catalog or stock | Purchase blocked or reconfirmed | `test_two_buyers_racing_for_the_last_unit_cannot_both_capture`, `test_stock_runs_out` | Passing |  |
| Unauthorized data access | Denied and recorded | `test_one_business_cannot_read_another_businesss_evidence`, `test_wrong_password_is_refused_and_audited` | Passing |  |
| Duplicate webhook | Idempotent processing | `test_webhook_is_processed_only_when_paypal_confirms_it_and_only_once` | Passing |  |
| Declined or canceled PayPal transaction | No false successful-payment status | `test_a_declined_capture_is_refused`, `test_a_cancelled_checkout_is_never_captured`, `test_a_denied_capture_webhook_never_shows_as_paid`, `test_returning_without_approving_does_not_mark_paid` | Passing |  |
| Consent withdrawn | New disclosures cease and credentials are updated appropriately | `test_withdrawing_consent_revokes_the_passport_and_hides_the_record`, `test_a_shop_that_takes_its_passport_down_is_shown_as_withdrawn_not_unknown` | Passing |  |
| A sealed shop turns out to be a scam | Seal withdrawn for cause: check fails, shoppers and agents told why, no checkout, nobody else affected | `test_withdrawing_needs_the_admin_token`, `test_withdraw_for_cause_end_to_end` | Passing |  |
| Evidence switch leaks evidence into the baseline | With evidence off, no standing, seal, hint or warning reaches the model or the page | `test_search_with_evidence_off_carries_no_trust_information`, `test_a_model_cannot_switch_the_baseline_off_or_on`, `test_chat_api_evidence_off_offline_has_no_standing`, `test_gemini_loop_follows_the_function_calling_protocol` | Passing |  |
| Model recommends an unsupported product | Safe refusal or correction | `test_no_checkout_for_a_shop_without_paypal` | Passing | Code refuses the checkout. The model saying 'nothing fits' is graded by evals/tau task nothing-fits, which has not been run with a model. |
| Refund after credential issuance | Dependent metrics become eligible for recalculation | `test_a_confirmed_paypal_order_joins_the_record_and_a_refund_recalculates_it` | Passing |  |

## Not verified

- Live PayPal sandbox calls (checkout, tracking, refund, webhook verification) are exercised against a stand-in for PayPal's API.
- The assistant has not been run with a live model on this build; the 50-task result is the recorded run of 2026-11-10.
- promptfoo and ArkSim configurations are written but have not been run.
- The container image and Render deployment have not been built or deployed.

## Runs

- data_platform/tests: 55 passed in 5.74s
- api/tests: 108 passed, 2 skipped in 78.88s (0:01:18)
- evals/tau harness: oracle: pass rate 0.917, pass^1 0.917 over 12 tasks
- evals/tau harness: naive: pass rate 0.0, pass^1 0.0 over 12 tasks
