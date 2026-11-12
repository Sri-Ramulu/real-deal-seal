H = {"Accept": "application/json, text/event-stream"}


def test_health_reports_modes_honestly(client):
    h = client.get("/api/health").json()
    assert h["gates_green"] and h["assistant"] == "offline" and set(h["checkout"].values()) == {"simulated"}


def test_scorecard_north_star_matches_the_graded_run(client):
    """The headline is read from the recorded evaluation, never typed in: it must equal the grader's summary."""
    import json
    from pathlib import Path
    s = json.loads((Path(__file__).resolve().parents[2] / "data_platform/landing/agent/summary.json").read_text())["by_model"]["claude-sonnet-5-5"]
    ns = client.get("/api/scorecard").json()["north_star"]
    assert (ns["numerator"], ns["baseline_numerator"], ns["denominator"]) == (s["verified"]["by_kind"].get("small", 0), s["baseline"]["by_kind"].get("small", 0), 50)
    assert (ns["withdrawn"], ns["baseline_withdrawn"]) == (s["verified"]["by_kind"].get("scam", 0), s["baseline"]["by_kind"].get("scam", 0))
    assert ns["lift_points"] == ns["value"] - ns["baseline"] and "not purchases" in ns["caveat"]


def test_every_kpi_names_its_source(client):
    sc = client.get("/api/scorecard").json()
    assert len(sc["perspectives"]) == 4 and all(k["source"] for p in sc["perspectives"] for k in p["kpis"])


def test_verify_endpoint_spots_an_edit(client):
    cred = client.get("/api/merchants/lydia/seal").json()
    assert client.post("/api/verify", json={"credential": cred}).json()["genuine"]
    cred["credentialSubject"]["name"] = "Linen Palace"
    assert client.post("/api/verify", json={"credential": cred}).json()["result"] == "edited"


def test_did_document_publishes_the_key(client):
    d = client.get("/.well-known/did.json").json()
    assert d["verificationMethod"][0]["publicKeyMultibase"] == client.get("/api/issuer-key").json()["publicKeyMultibase"]


def test_offline_assistant_says_it_is_offline(client):
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "lavender napkins"}]}).json()
    assert r["mode"] == "offline" and r["answer"].startswith("Offline mode") and r["offers"]


def test_mcp_lists_the_eight_tools(client):
    r = client.post("/mcp/", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, headers=H)
    assert sorted(t["name"] for t in r.json()["result"]["tools"]) == sorted(
        ["search_products", "get_merchant_passport", "check_any_shop", "verify_seal", "get_criteria",
         "find_sealed_alternative", "compare_market_prices", "create_checkout"])


def test_mcp_tool_call_returns_the_passport(client):
    r = client.post("/mcp/", json={"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                   "params": {"name": "get_merchant_passport", "arguments": {"shop_id": "lydia"}}}, headers=H)
    assert "Real Deal: sealed" in r.json()["result"]["content"][0]["text"]


def test_semantic_endpoint_refuses_unknown_measures(client):
    assert client.get("/api/platform/metric?view=commerce_metrics&measures=made_up").status_code == 400


def test_unknown_shop_is_a_404_with_an_honest_message(client):
    r = client.get("/api/merchants/nobody")
    assert r.status_code == 404 and "cannot vouch" in r.json()["detail"]


def test_evidence_rows_are_private_and_carry_no_buyer_identity(client):
    assert client.get("/api/studio/lydia/evidence").status_code == 401
    tok = client.post("/api/auth/login", json={"email": "lydia@demo.realdealseal.example", "password": "demo-owner"}).json()["token"]
    row = client.get("/api/studio/lydia/evidence", headers={"Authorization": f"Bearer {tok}"}).json()[0]
    assert not {"payer", "payer_key", "buyer", "email", "city"} & set(row)


def test_public_passport_has_no_order_rows(client):
    p = client.get("/api/merchants/lydia").json()
    assert set(p) == {"passport", "facts", "rules", "seal", "products", "record_shape"} and "order_id" not in str(p)
