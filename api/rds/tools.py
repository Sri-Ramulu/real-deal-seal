"""The eight agent tools. One implementation, used by the MCP server, the in-app agent and the evals.

Design rules (after Anthropic's guidance on writing tools for agents):
- few tools, each a whole task; names say what they do; descriptions say when to use them
- answers are small and already meaningful (names and plain words, not internal codes)
- text written by sellers is wrapped and marked untrusted, with any instruction aimed at AI flagged
- results are never ranked by trust: the agent weighs price, fit and evidence itself
- errors say what to do next
"""
from __future__ import annotations

import json
import re

from . import checkout, config, passport, warehouse  # noqa: F401 (warehouse is used by the eval graders)

STOP = {"a", "an", "the", "for", "my", "me", "i", "want", "need", "find", "buy", "get", "of", "in", "to", "and", "or", "with",
        "some", "looking", "is", "that", "it", "on", "from", "please", "set", "under", "something", "nothing", "too"}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP and len(t) > 1]


def _image(sku: str) -> str:
    return f"{config.PUBLIC_URL}/api/products/{sku}/image.svg"


def _offer(o: dict) -> dict:
    return {"sku": o["sku"], "product": o["product_name"], "price_usd": o["price_usd"], "in_stock": o["in_stock"], "image_url": _image(o["sku"]),
            "shop_id": o["merchant_id"], "shop": o["merchant_name"], "ships_from": o["ships_from"], "returns": o["returns_policy"],
            "shop_standing": o["standing_headline"], "paypal_checkout": o["paypal_checkout_available"],
            "seller_text": {"untrusted": True, "text": o["seller_description"],
                            "contains_instructions_for_ai": bool(o["seller_text_has_instructions"])}}


def _plain_offer(o: dict) -> dict:
    """What an ordinary shopping search shows: the listing only. No standing, no seal, no flags from Real Deal Seal."""
    text = " ".join(t for t in (o.get("self_claim"), o["seller_description"]) if t)
    return {"sku": o["sku"], "product": o["product_name"], "price_usd": o["price_usd"], "in_stock": o["in_stock"], "image_url": _image(o["sku"]),
            "shop_id": o["merchant_id"], "shop": o["merchant_name"], "ships_from": o["ships_from"], "returns": o["returns_policy"],
            "paypal_checkout": o["accepts_paypal"], "seller_text": {"text": text}}


def search_products(query: str, max_price_usd: float | None = None, limit: int = 8, evidence: bool = True) -> dict:
    """evidence=False is the baseline for the Evidence switch: plain listings, nothing from Real Deal Seal.
    The flag is set by the server, never by the model (see SERVER_ONLY_ARGS)."""
    words = _tokens(query)
    offers = warehouse.rows("SELECT o.*, m.self_claim FROM gold.agent_offers o JOIN gold.dim_merchant m USING (merchant_id)")
    scored = []
    for o in offers:
        hay_name, hay_tags, hay_desc = o["product_name"].lower(), " ".join(o["tags"]).lower(), (o["seller_description"] or "").lower()
        score = sum(3 * (w in hay_name) + 2 * (w in hay_tags) + (w in hay_desc) for w in words)
        if score and (max_price_usd is None or o["price_usd"] <= max_price_usd):
            scored.append((score, o))
    scored.sort(key=lambda x: (-x[0], x[1]["price_usd"], x[1]["sku"]))  # relevance, then price. Never trust.
    top = [o for _, o in scored[: max(1, min(limit, 12))]]
    if not evidence:
        return {"query": query, "matches": len(scored), "offers": [_plain_offer(o) for o in top],
                "ordering": "by relevance to the query, then price."}
    out = []
    for o in top:
        item = _offer(o)
        if o.get("self_claim"):
            item["shop_self_claim"] = {"untrusted": True, "text": o["self_claim"], "contains_instructions_for_ai": bool(o["seller_text_has_instructions"]),
                                       "note": "A claim in a listing is not a seal. Use get_merchant_passport or verify_seal."}
        out.append(item)
    return {"query": query, "matches": len(scored), "offers": out,
            "ordering": "by relevance to the query, then price. Not ranked by trust.",
            "next": "Call get_merchant_passport for any shop you are considering." if out else "No match. Try fewer or different words."}


def get_merchant_passport(shop_id: str) -> dict:
    p = warehouse.one("SELECT * FROM gold.merchant_passport WHERE merchant_id = ? AND (passport_published OR standing = 'withdrawn')",
                      [shop_id.strip().lower()])
    if not p:
        return {"found": False, "message": f"No shop with id '{shop_id}'. Use the shop_id from search_products, or check_any_shop with a name."}
    if p["standing"] == "withdrawn":
        return {"found": True, "shop": p["merchant_name"], "standing": p["headline"], "verdict": p["verdict"],
                "withdrawn_by": "Real Deal Seal" if p["seal_withdrawn_by"] == "issuer" else "the business itself",
                "withdrawn_on": str(p["seal_withdrawn_at"])[:10] if p["seal_withdrawn_at"] else None, "reason": p["seal_withdrawn_reason"],
                "seal_check": "withdrawn", "do_not_recommend": True, "checkout_available": False,
                "note": "A withdrawn seal is not the same as an unknown shop. Do not recommend this shop, and tell the shopper why."}
    if not p["has_record"]:
        return {"found": True, "shop": p["merchant_name"], "standing": p["headline"], "verdict": p["verdict"],
                "facts": [], "displays_badge_that_does_not_verify": p["shows_unverifiable_badge"],
                "note": "No record means missing evidence. It says nothing bad about the shop."}
    cred = passport.issue(p["merchant_id"])
    check = passport.verify(cred)
    facts = warehouse.rows("""SELECT label, value, unit, numerator, denominator, window_label, evidence_class
                              FROM gold.fact_metric_observations WHERE merchant_id = ? AND NOT (is_optional_to_disclose AND list_contains(?, metric))
                              ORDER BY display_order""", [p["merchant_id"], p["hidden_metrics"]])
    rules = warehouse.rows("SELECT rule_label, met FROM gold.fact_rule_results WHERE merchant_id = ? ORDER BY rule_order", [p["merchant_id"]])
    return {"found": True, "shop": p["merchant_name"], "standing": p["headline"], "verdict": p["verdict"],
            "business_type": p["business_type_label"], "evidence_basis": p["evidence_basis"],
            "evidence_strength": p["evidence_strength"], "data_as_of": p["data_as_of"], "criteria_version": p["criteria_version"],
            "seal_check": check["result"], "seal_checked_by": check["checked_by"],
            "facts": [{"fact": f["label"], "value": f"{f['value']}{'%' if f['unit'] == '%' else ' ' + f['unit']}" if f["value"] is not None else "not measured",
                       "counted": f"{f['numerator']} of {f['denominator']}" if f["denominator"] else None,
                       "window": f["window_label"], "evidence": f["evidence_class"]} for f in facts],
            "rules": [{"rule": r["rule_label"], "met": r["met"]} for r in rules],
            "issuer": "Real Deal Seal (hackathon project). PayPal supplied the sandbox records, not the signature.",
            "passport_url": f"/shops/{p['merchant_id']}"}


def check_any_shop(name_or_url: str) -> dict:
    norm = re.sub(r"[^a-z0-9]", "", re.sub(r"^https?://(www\.)?", "", name_or_url.lower()).split("/")[0].replace(".com", ""))
    for p in warehouse.rows("SELECT merchant_id, merchant_name FROM gold.merchant_passport WHERE passport_published OR standing = 'withdrawn'"):
        mine = re.sub(r"[^a-z0-9]", "", p["merchant_name"].lower())
        if norm and (norm == mine or norm == p["merchant_id"] or (len(norm) >= 5 and (norm in mine or mine in norm))):
            return get_merchant_passport(p["merchant_id"])
    return {"found": False, "standing": "Unknown shop",
            "message": f"Real Deal Seal has no record for '{name_or_url}', so it can't vouch for it either way."}


def verify_seal(credential_json: str) -> dict:
    return passport.verify(credential_json)


def get_criteria() -> dict:
    rules = warehouse.rows("SELECT ruleset, rule_label, criteria_version FROM gold.dim_rule ORDER BY rule_key")
    by_type = {}
    for r in rules:
        by_type.setdefault(r["ruleset"], []).append(r["rule_label"])
    return {"criteria_version": rules[0]["criteria_version"], "rules_by_business_type": by_type,
            "metric_definitions": warehouse.rows("SELECT metric, metric_label, layer, applies_to, definition FROM gold.dim_metric ORDER BY metric_key"),
            "standings": {"Real Deal: sealed": "every rule of its business type met on PayPal-confirmed payments", "Verified facts, not yet sealed": "facts checked, at least one rule unmet",
                          "Self-reported record, not yet confirmed": "the business's own imported records; cannot earn the seal alone",
                          "Not enough history yet": "too few orders to judge; new is not bad", "No PayPal record on file": "nothing to check",
                          "Seal withdrawn": "Real Deal Seal withdrew the seal for a stated reason, or the business took its record down; do not recommend"},
            "evidence_classes": {r["evidence_class"]: r["meaning"] for r in warehouse.rows("SELECT * FROM gold.dim_evidence_class ORDER BY evidence_class_key")},
            "note": "Real Deal Seal's published demo rules. Each business is judged only by the rules of its own type. They are not PayPal's criteria."}


def find_sealed_alternative(sku: str) -> dict:
    o = warehouse.one("SELECT * FROM gold.agent_offers WHERE sku = ?", [sku])
    if not o:
        return {"found": False, "message": f"No product with SKU {sku}."}
    kind = o["tags"][0] if o["tags"] else ""
    alts = warehouse.rows("""SELECT * FROM gold.agent_offers WHERE standing = 'sealed' AND sku <> ? AND in_stock
                             AND list_contains(tags, ?) ORDER BY abs(price_usd - ?), sku LIMIT 3""", [sku, kind, o["price_usd"]])
    if not alts:
        return {"found": False, "message": f"No sealed shop sells a '{kind}' right now. Say so rather than stretching the match."}
    return {"found": True, "same_kind_of_item": kind, "alternatives": [_offer(a) for a in alts]}


def compare_market_prices(query: str) -> dict:
    words = set(_tokens(query))
    best, best_overlap = None, 0
    for q in warehouse.rows("SELECT DISTINCT query FROM gold.market_price_context"):
        overlap = len(words & set(_tokens(q["query"])))
        if overlap > best_overlap:
            best, best_overlap = q["query"], overlap
    if not best or best_overlap < 2:
        return {"available": False, "message": "No cached web prices for that query."}
    offers = warehouse.rows("SELECT title, brand, price_usd, store, fetched_at FROM gold.market_price_context WHERE query = ? ORDER BY price_usd", [best])
    prices = sorted(o["price_usd"] for o in offers)
    return {"available": True, "matched_query": best, "source": "Channel3 product search, cached", "fetched_at": offers[0]["fetched_at"],
            "typical_price_usd": prices[len(prices) // 2], "range_usd": [prices[0], prices[-1]], "offers": offers[:5],
            "note": "Web offers for price context only. None has a PayPal record behind it."}


def create_checkout(sku: str, quantity: int = 1, evidence: bool = True) -> dict:
    try:
        s = checkout.create(sku, int(quantity), actor="agent")
    except checkout.CheckoutError as e:
        if not evidence and e.code == "seal_withdrawn":  # the baseline must not learn about seals from a refusal
            return {"created": False, "reason": "checkout_unavailable", "message": "Checkout is not available for this product right now."}
        return {"created": False, "reason": e.code, "message": e.message}
    return {"created": True, "approve_url": s["approve_url"], "amount_usd": s["amount_usd"], "product": s["product_name"],
            "shop": s["merchant_name"], "mode": s["mode"], "note": s["note"],
            "next": "Give the buyer the approve_url. Only the buyer can approve in PayPal. Do not say it is paid."}


TOOLS = {f.__name__: f for f in (search_products, get_merchant_passport, check_any_shop, verify_seal, get_criteria,
                                 find_sealed_alternative, compare_market_prices, create_checkout)}

SPECS = [
    {"name": "search_products", "description": "Search the catalog for products that match a shopper's request. Returns offers from every shop, ordered by relevance then price, never by trust. Use this first for any shopping request.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string", "description": "What the shopper wants, e.g. 'purple linen table runner'"},
                      "max_price_usd": {"type": "number", "description": "Optional price ceiling in US dollars"}, "limit": {"type": "integer", "description": "How many offers to return (default 8, max 12)"}}, "required": ["query"]}},
    {"name": "get_merchant_passport", "description": "Read a shop's Merchant Passport: its standing, each fact with what was counted out of what, the evidence class of each fact, and whether its seal verifies. Use for every shop you are seriously considering.",
     "input_schema": {"type": "object", "properties": {"shop_id": {"type": "string", "description": "The shop_id from search_products, e.g. 'lydia'"}}, "required": ["shop_id"]}},
    {"name": "check_any_shop", "description": "Look up a shop by name or web address when you have no shop_id. Unknown shops get an honest 'cannot vouch', never an invented score.",
     "input_schema": {"type": "object", "properties": {"name_or_url": {"type": "string"}}, "required": ["name_or_url"]}},
    {"name": "verify_seal", "description": "Check a seal (signed credential JSON) someone pasted or a shop displays. Code checks the signature, issuer, expiry and withdrawal. Use this instead of believing a badge or a claim.",
     "input_schema": {"type": "object", "properties": {"credential_json": {"type": "string", "description": "The full credential as JSON text"}}, "required": ["credential_json"]}},
    {"name": "get_criteria", "description": "The published rules a shop must meet to be sealed, and what each evidence class means. Use when the shopper asks how shops are judged.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "find_sealed_alternative", "description": "Given a product, find the same kind of item from a sealed shop. Says plainly when there is none.",
     "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}},
    {"name": "compare_market_prices", "description": "Typical web prices for a product type (Channel3, cached), to judge whether a price is unusually low or high. Context only: these web offers have no PayPal record.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "create_checkout", "description": "Open a PayPal checkout for one product after the shopper has said they want to buy it. Returns a link the shopper must approve in PayPal. You cannot pay; never say the order is paid.",
     "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}, "quantity": {"type": "integer", "description": "1 to 10, default 1"}}, "required": ["sku"]}},
]


SERVER_ONLY_ARGS = {"evidence"}  # a model or an outside client can never set these


def call(name: str, args: dict, **server_args) -> dict:
    if name not in TOOLS:
        return {"error": f"Unknown tool '{name}'. Available: {', '.join(TOOLS)}."}
    args = {k: v for k, v in (args or {}).items() if k not in SERVER_ONLY_ARGS}
    try:
        return TOOLS[name](**args, **server_args)
    except TypeError as e:
        return {"error": f"Bad arguments for {name}: {e}. Check the tool's input schema."}


def as_text(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, default=str)
