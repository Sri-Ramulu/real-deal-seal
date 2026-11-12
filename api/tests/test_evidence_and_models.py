"""The Evidence switch and the model choice.

Evidence off must be a true baseline: no standing, seal, self-claim note, AI-instruction flag or passport hint
reaches the model or the page. The model choice must reach the right provider, and the Gemini loop must follow
the function-calling protocol (send the model's turn back unchanged, answer each call by name and id).
"""
import json
from types import SimpleNamespace

import httpx
import pytest

from rds import agent, config, tools

TRUST_KEYS = {"shop_standing", "shop_self_claim", "standing", "seal_check", "next"}


def _walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_keys(v)


def test_search_with_evidence_off_carries_no_trust_information(client):
    off = tools.search_products("linen table runner", evidence=False)
    assert off["offers"], "the baseline must still find products"
    keys = set(_walk_keys(off))
    assert not keys & TRUST_KEYS
    assert "contains_instructions_for_ai" not in keys and "untrusted" not in keys
    text = json.dumps(off).lower()
    for word in ("sealed", "passport", "verified facts", "no paypal record"):
        assert word not in text, word


def test_search_with_evidence_on_keeps_trust_information(client):
    on = tools.search_products("linen table runner")
    assert all("shop_standing" in o for o in on["offers"])
    assert "next" in on


def test_baseline_still_shows_a_sellers_own_claims_as_listing_text(client):
    off = tools.search_products("runner", evidence=False)
    palace = [o for o in off["offers"] if o["shop_id"] == "palace"]
    on = [o for o in tools.search_products("runner")["offers"] if o["shop_id"] == "palace"]
    if palace and on and on[0].get("shop_self_claim"):
        assert on[0]["shop_self_claim"]["text"] in palace[0]["seller_text"]["text"]


def test_a_model_cannot_switch_the_baseline_off_or_on(client):
    r = tools.call("search_products", {"query": "napkins", "evidence": False})
    assert all("shop_standing" in o for o in r["offers"]), "the model must not be able to choose the baseline itself"
    r = tools.call("search_products", {"query": "napkins", "evidence": True}, evidence=False)
    assert not any("shop_standing" in o for o in r["offers"])


def test_chat_api_evidence_off_offline_has_no_standing(client):
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "purple table runner"}], "evidence": False}).json()
    assert r["mode"] == "offline" and r["evidence"] is False
    assert r["offers"] and not any("shop_standing" in o for o in r["offers"])
    assert "Sealed" not in r["answer"] and "sealed" not in r["answer"]


def test_health_lists_the_three_models_with_gemini_default(client):
    h = client.get("/api/health").json()
    keys = [m["key"] for m in h["models"]]
    assert keys == ["gemini", "claude-sonnet", "claude-haiku"], "no Opus in the menu"
    assert [m["key"] for m in h["models"] if m["default"]] == ["gemini"]
    assert h["assistant"] == "offline"  # no keys in the test run


def test_model_resolution_and_fallback(monkeypatch):
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    assert config.resolve_model(None) is None
    monkeypatch.setattr(config, "GEMINI_API_KEY", "g")
    assert config.resolve_model(None)["key"] == "gemini"
    assert config.resolve_model("claude-haiku")["key"] == "gemini", "an unavailable choice falls back to one that works"
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "a")
    assert config.resolve_model("claude-haiku")["model"] == config.HAIKU_MODEL
    assert config.resolve_model("claude-sonnet")["model"] == config.MODEL
    assert config.resolve_model(config.HAIKU_MODEL)["key"] == "claude-haiku", "a raw id works for a model on the menu"
    assert config.resolve_model("claude-opus-5-5")["key"] == "gemini", "a model off the menu cannot be reached"
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    assert config.resolve_model(None)["key"] == "claude-sonnet", "with no Gemini key the default falls back to Claude"


class FakeGemini:
    """Stands in for generativelanguage.googleapis.com: first asks for a search, then answers with a pick."""

    def __init__(self):
        self.requests = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        self.requests.append({"url": str(request.url), "key": request.headers.get("x-goog-api-key"), "body": body})
        if len(self.requests) == 1:
            parts = [{"functionCall": {"name": "search_products", "args": {"query": "purple table runner"}, "id": "call-1"},
                      "thoughtSignature": "sig-abc"}]
        else:
            parts = [{"text": "I'd pick the runner.\nPICK: JF-RUN-PL"}]
        return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": parts}, "finishReason": "STOP"}],
                                         "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 20}})


@pytest.fixture
def gemini(monkeypatch, client):
    fake = FakeGemini()
    real = httpx.Client
    monkeypatch.setattr(agent.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(fake.handler), **kw))
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    return fake


@pytest.mark.parametrize("evidence", [True, False])
def test_gemini_loop_follows_the_function_calling_protocol(gemini, evidence):
    r = agent.chat([{"role": "user", "content": "I want a purple table runner"}], evidence=evidence)
    assert r["mode"] == "gemini" and r["model"] == config.GEMINI_MODEL and r["model_label"] == "Google Gemini"
    assert r["pick"] == "JF-RUN-PL" and "PICK" not in r["answer"]
    assert [t["tool"] for t in r["trace"]] == ["search_products"]
    assert r["usage"] == {"input_tokens": 200, "output_tokens": 40}
    first, second = gemini.requests
    assert first["key"] == "test-key" and first["url"].endswith(f"/models/{config.GEMINI_MODEL}:generateContent")
    declared = [d["name"] for d in first["body"]["tools"][0]["functionDeclarations"]]
    assert declared == (["search_products", "create_checkout"] if evidence is False else [s["name"] for s in tools.SPECS])
    system = first["body"]["systemInstruction"]["parts"][0]["text"]
    assert ("passport" in system) is evidence
    echoed = second["body"]["contents"][1]
    assert echoed["role"] == "model" and echoed["parts"][0]["thoughtSignature"] == "sig-abc", "the model's turn must return unchanged"
    reply = second["body"]["contents"][2]["parts"][0]["functionResponse"]
    assert reply["name"] == "search_products" and reply["id"] == "call-1"
    offers = reply["response"]["result"]["offers"]
    assert offers and all(("shop_standing" in o) is evidence for o in offers)


def test_gemini_error_becomes_a_clear_api_message(monkeypatch, client):
    monkeypatch.setattr(agent, "BUSY_WAITS", (0, 0))
    real = httpx.Client
    monkeypatch.setattr(agent.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(lambda req: httpx.Response(429, text="quota")), **kw))
    monkeypatch.setattr(config, "GEMINI_API_KEY", "k")
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "napkins"}]})
    assert r.status_code == 502 and "did not answer" in r.json()["detail"]


def _fake_claude(monkeypatch, seen):
    class FakeMessages:
        def create(self, **kw):
            seen.update(kw)
            return SimpleNamespace(usage=SimpleNamespace(input_tokens=5, output_tokens=3), stop_reason="end_turn",
                                   content=[SimpleNamespace(type="text", text="The runner.\nPICK: JF-RUN-PL")])

    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: SimpleNamespace(messages=FakeMessages()))


def _gemini_answers(monkeypatch, statuses):
    """Gemini answers with each status in turn; a 200 is a final answer."""
    calls = []

    def handler(req):
        status = statuses[min(len(calls), len(statuses) - 1)]
        calls.append(status)
        if status != 200:
            return httpx.Response(status, text='{"error": {"message": "This model is currently experiencing high demand."}}')
        parts = [{"text": "I'd pick the runner.\nPICK: JF-RUN-PL"}]
        return httpx.Response(200, json={"candidates": [{"content": {"role": "model", "parts": parts}}]})

    real = httpx.Client
    monkeypatch.setattr(agent.httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    monkeypatch.setattr(agent, "BUSY_WAITS", (0, 0))
    monkeypatch.setattr(config, "GEMINI_API_KEY", "k")
    return calls


def test_busy_gemini_is_retried_before_giving_up(monkeypatch, client):
    calls = _gemini_answers(monkeypatch, [503, 503, 200])
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    r = agent.chat([{"role": "user", "content": "runner"}])
    assert calls == [503, 503, 200] and r["mode"] == "gemini" and r["busy_from"] is None and r["pick"] == "JF-RUN-PL"


@pytest.mark.parametrize("evidence", [True, False])
def test_gemini_still_busy_hands_over_to_claude_sonnet_and_says_so(monkeypatch, client, evidence):
    calls = _gemini_answers(monkeypatch, [503])
    seen = {}
    _fake_claude(monkeypatch, seen)
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "a")
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "runner"}], "evidence": evidence}).json()
    assert calls == [503, 503, 503], "two retries, then hand over"
    assert r["mode"] == "claude" and r["model"] == config.MODEL and r["busy_from"] == "Google Gemini"
    assert r["model_label"] == "Claude Sonnet (Google Gemini was busy)" and r["evidence"] is evidence
    assert ("passport" in seen["system"]) is evidence, "the hand-over keeps the Evidence setting"


def test_an_evaluation_can_refuse_the_hand_over(monkeypatch, client):
    _gemini_answers(monkeypatch, [503])
    _fake_claude(monkeypatch, {})
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "a")
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "runner"}], "fallback": False})
    assert r.status_code == 502, "with fallback off, a busy Gemini is reported, never answered by another model"


def test_busy_gemini_without_claude_is_a_clear_error(monkeypatch, client):
    _gemini_answers(monkeypatch, [503])
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "runner"}]})
    assert r.status_code == 502 and "did not answer" in r.json()["detail"]


def test_claude_haiku_choice_reaches_anthropic_with_the_haiku_model(monkeypatch, client):
    seen = {}

    class FakeMessages:
        def create(self, **kw):
            seen.update(kw)
            return SimpleNamespace(usage=SimpleNamespace(input_tokens=5, output_tokens=3), stop_reason="end_turn",
                                   content=[SimpleNamespace(type="text", text="Nothing fits.\nPICK: none")])

    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: SimpleNamespace(messages=FakeMessages()))
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "k")
    r = client.post("/api/chat", json={"messages": [{"role": "user", "content": "a sofa"}], "model": "claude-haiku", "evidence": False}).json()
    assert seen["model"] == config.HAIKU_MODEL and r["model_label"] == "Claude Haiku" and r["pick"] is None
    assert [t["name"] for t in seen["tools"]] == ["search_products", "create_checkout"]
    assert "passport" not in seen["system"]


def test_every_product_has_an_image_and_every_shop_gets_the_same_treatment(client):
    from rds import product_art, warehouse
    products = warehouse.rows("SELECT sku, product_name, tags, merchant_id FROM gold.dim_product")
    assert products
    for p in products:
        r = client.get(f"/api/products/{p['sku']}/image.svg")
        assert r.status_code == 200 and r.headers["content-type"].startswith("image/svg+xml")
        assert r.text.startswith("<svg") and p["product_name"].split(",")[0] in r.text, "the image carries the product name as its label"
        kind, _, _ = product_art.classify(p["product_name"], p["tags"])
        assert kind in product_art.DRAW or kind in product_art.DRAW_NAMED
    assert client.get("/api/products/NOPE/image.svg").status_code == 404
    offer = tools.search_products("napkins")["offers"][0]
    assert offer["image_url"].endswith(f"/api/products/{offer['sku']}/image.svg")
    assert tools.search_products("napkins", evidence=False)["offers"][0]["image_url"]
