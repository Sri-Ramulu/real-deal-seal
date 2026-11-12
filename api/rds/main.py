"""HTTP API. Thin: every route reads gold through warehouse.py or calls one module.

Public routes return aggregated, consented facts only. Everything under /api/studio/{merchant_id} is private to
that business and goes through auth.require_merchant.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import re
import os
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import agent, auth, checkout, coach, config, demo_shops, onboarding, passport, product_art, refresh, scorecard, statement, store, studio, tools, webhooks, warehouse as wh
from .mcp_server import http_app as mcp_app, mcp


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    wh.con()
    store.db()
    auth.seed_demo_owners()
    if config.DEMO_SHOPS:
        demo_shops.ensure()
    if refresh.stale():  # a deploy changed the pipeline or its landing data: rebuild instead of serving the old warehouse
        refresh.run("startup: new build")
    refresh.reconcile_credentials()
    task = asyncio.create_task(_scheduled_refresh()) if config.REFRESH_HOURS > 0 else None
    async with mcp.session_manager.run():
        yield
    if task:
        task.cancel()


async def _scheduled_refresh():
    """Recalculate every record on a timer, so a standing changes without anyone pressing Refresh."""
    while True:
        await asyncio.sleep(config.REFRESH_HOURS * 3600)
        try:
            await asyncio.to_thread(refresh.run, "scheduled")
        except Exception as e:  # keep the timer alive; the failure is recorded in the jobs table by refresh.run
            store.audit("scheduler", "pipeline.refresh", result="failed", detail={"error": str(e)[:300]})


app = FastAPI(title="Real Deal Seal API", version="2.0.0", lifespan=lifespan,
              description="Merchant evidence for AI shopping: signed passports from PayPal sandbox records, agent tools, PayPal checkout, "
                          "and a private studio for each business. Public routes return aggregated, consented facts only.")
app.mount("/mcp", mcp_app)

_STUDIO = re.compile(r"^/api/studio/([^/]+)")


@app.middleware("http")
async def tenant_scope(request: Request, call_next):
    """Every /api/studio/{business} request runs scoped to that business, so on PostgreSQL row-level security
    returns only its rows even if a query forgets its filter. Authorization is still checked by the route."""
    m = _STUDIO.match(request.url.path)
    if not m:
        return await call_next(request)
    with store.tenant(m.group(1)):
        return await call_next(request)
Owner = Depends(auth.require_merchant)


class ChatIn(BaseModel):
    messages: list[dict] = Field(..., description="[{role, content}] with the shopper's latest message last")
    evidence: bool = Field(True, description="False is the baseline: plain product search only, no passports, seals or standings")
    model: str | None = Field(None, description="'gemini', 'claude-sonnet' or 'claude-haiku'; empty uses the server's default")
    fallback: bool = Field(True, description="If Gemini is busy, answer with Claude Sonnet. Evaluations set this to false so every answer comes from the model asked for.")


class CheckoutIn(BaseModel):
    sku: str
    quantity: int = 1
    idempotency_key: str | None = None


class VerifyIn(BaseModel):
    credential: dict | str


class LoginIn(BaseModel):
    email: str
    password: str


class WorkspaceIn(BaseModel):
    name: str
    business_type: str = Field(..., description="physical, services, digital or local")
    email: str
    password: str
    category: str | None = None
    region: str | None = "US"
    sells: str | None = None
    ships_from: str | None = None
    returns_policy: str | None = None


class ImportIn(BaseModel):
    rows: list[dict] | None = Field(None, description="Rows as JSON objects")
    csv: str | None = Field(None, description="Or the file's text, with a header row")
    simulated_demo: bool = Field(False, description="Mark the file as invented demo data; its facts are then labelled simulated")


class DisclosureIn(BaseModel):
    publish: bool
    hidden_metrics: list[str] = []


class TrackingIn(BaseModel):
    order_id: str
    tracking_number: str
    carrier: str = "OTHER"


class ShareIn(BaseModel):
    recipient: str
    purpose: str


@app.exception_handler(checkout.CheckoutError)
async def checkout_error(_, e: checkout.CheckoutError):
    return JSONResponse({"error": e.code, "message": e.message}, status_code=409 if e.code in ("out_of_stock", "not_approved", "already_refunded") else 400)


# ---- public: status and discovery ------------------------------------------------------------------------------
@app.get("/api/health")
def health():
    cat = wh.catalog()
    last = store.one("SELECT status, last_error, updated_at FROM jobs ORDER BY job_id DESC LIMIT 1")
    d = config.resolve_model(None) or {}
    return {"ok": True, "pipeline_run": cat["run_id"], "gates_green": all(g["failed"] == 0 for g in cat["gates"]),
            "last_refresh": last, "assistant": d.get("provider", "offline"),
            "model": d.get("model"), "model_label": d.get("label"), "default_model": d.get("key"), "models": config.model_choices(),
            "checkout": {m["merchant_id"]: checkout.mode_for(m["merchant_id"]) for m in wh.rows("SELECT merchant_id FROM gold.dim_merchant WHERE is_connected")}}


@app.get("/api/health/deep")
def health_deep():
    """Checks the operational database itself: which backend, whether every migration has run, and row-level security."""
    h = store.health()
    ok = h["schema_current"] and (h["row_level_security"] is None or all(h["row_level_security"].values()))
    return JSONResponse({"ok": ok, **h}, status_code=200 if ok else 503)


@app.get("/api/business-types")
def business_types():
    rules = wh.rows("SELECT ruleset, rule_label FROM gold.dim_rule ORDER BY rule_key")
    return [{**b, "rules": [r["rule_label"] for r in rules if r["ruleset"] == b["ruleset"]]}
            for b in wh.rows("SELECT * FROM silver.merchant_business_types")]


@app.get("/api/merchants")
def merchants():
    rows = wh.rows("SELECT * FROM gold.merchant_passport WHERE passport_published OR standing = 'withdrawn' "
                   "ORDER BY standing = 'withdrawn', has_record DESC, orders_completed DESC NULLS LAST, merchant_name")
    return [r if r["passport_published"] else {k: r[k] for k in ("merchant_id", "merchant_name", "merchant_kind", "origin", "business_type_label",
                                                                 "standing", "headline", "verdict", "seal_withdrawn_by", "seal_withdrawn_at",
                                                                 "seal_withdrawn_reason", "passport_published")} | {"has_record": False}
            for r in rows]


@app.get("/api/merchants/{merchant_id}")
def merchant(merchant_id: str):
    p = studio.public_passport(merchant_id)
    if not p:
        raise HTTPException(404, "No published passport for that business. Real Deal Seal cannot vouch for a shop it has no public record of.")
    return p


@app.get("/api/merchants/{merchant_id}/seal")
def seal(merchant_id: str):
    if merchant_id == "palace":
        return passport.forged_sample()
    cred = passport.issue(merchant_id)
    if not cred:
        # A withdrawn shop may keep showing its last seal; hand that one back so anyone can watch it fail the check.
        last = store.one("SELECT document FROM credentials WHERE merchant_id = ? AND kind = 'passport' AND status = 'revoked' ORDER BY issued_at DESC LIMIT 1",
                         [merchant_id]) if (wh.one("SELECT standing FROM gold.merchant_passport WHERE merchant_id = ?", [merchant_id]) or {}).get("standing") == "withdrawn" else None
        if last:
            return json.loads(last["document"])
        raise HTTPException(404, "This business has no published record, so there is nothing signed to show.")
    return cred


@app.post("/api/verify")
def verify(body: VerifyIn):
    return passport.verify(body.credential)


@app.get("/api/credentials/status-list/revocation")
def credential_status_list():
    """W3C Bitstring Status List (revocation). Each seal names its position in credentialStatus."""
    return JSONResponse(passport.status_list_credential(), headers={"Cache-Control": "public, max-age=60"})


@app.get("/api/credentials/status")
def credential_status(id: str):
    return passport.status_of(id)


@app.get("/api/issuer-key")
def issuer_key():
    return {"issuer": config.did(), "name": config.ISSUER_NAME, "verificationMethod": passport.verification_method(),
            "publicKeyMultibase": passport.public_key_multibase(), "cryptosuite": "eddsa-jcs-2022",
            "all_keys": [{"id": v["id"], "publicKeyMultibase": v["publicKeyMultibase"]} for v in passport.did_document()["verificationMethod"]]}


@app.get("/.well-known/did.json")
def did_json():
    return passport.did_document()


@app.get("/api/criteria")
def criteria():
    return tools.get_criteria()


@app.get("/api/products/{sku}/image.svg", include_in_schema=False)
def product_image(sku: str):
    p = wh.one("SELECT product_name, tags FROM gold.dim_product WHERE sku = ?", [sku])
    if not p:
        raise HTTPException(404, f"No product with SKU {sku}.")
    return Response(product_art.svg(p["product_name"], p["tags"]), media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/products")
def products(q: str | None = None):
    if q:
        return tools.search_products(q, limit=12)["offers"]
    return [tools._offer(o) for o in wh.rows("SELECT * FROM gold.agent_offers ORDER BY merchant_id, sku")]


# ---- public: assistant and tools ---------------------------------------------------------------------------------
@app.post("/api/chat")
def chat(body: ChatIn, request: Request):
    auth.rate_limit(f"chat:{request.client.host if request.client else ''}", 30, 60)
    try:
        r = agent.chat(body.messages[-12:], evidence=body.evidence, model=body.model, fallback=body.fallback)
    except Exception as e:  # a provider outage should read as a message, not a crash
        raise HTTPException(502, f"The AI model did not answer: {str(e)[:200]}. Try again, or pick another model.")
    pick_shop = next((o["shop_id"] for o in r["offers"] if o["sku"] == r["pick"]), None)
    last_user = next((m["content"] for m in reversed(body.messages) if m.get("role") == "user"), "")
    store.insert("agent_decisions", {"decision_id": str(uuid.uuid4()), "at": store.now(), "request": str(last_user)[:500], "mode": r["mode"], "model": r["model"],
                                     "evidence_enabled": int(body.evidence), "pick_sku": r["pick"], "pick_merchant_id": pick_shop,
                                     "tools": [t["tool"] for t in r["trace"]], "answer": r["answer"][:2000]})
    return r


@app.post("/v1/chat/completions")
def chat_completions(body: dict):
    """OpenAI-style endpoint so simulators such as ArkSim and promptfoo can talk to the assistant."""
    msgs = [{"role": m["role"], "content": m["content"]} for m in body.get("messages", []) if m.get("role") in ("user", "assistant")]
    r = agent.chat(msgs[-12:], evidence=body.get("evidence", True), model=body.get("model"))
    text = r["answer"] + (f"\nPICK: {r['pick']}" if r.get("pick") else "\nPICK: none")
    return {"id": "rds-chat", "object": "chat.completion", "model": r.get("model") or "offline",
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": text}}],
            "rds": {"mode": r["mode"], "trace": r["trace"], "pick": r.get("pick")}}


@app.get("/api/tools")
def tool_specs():
    return tools.SPECS


@app.post("/api/tools/{name}")
def tool(name: str, args: dict, request: Request):
    """Call an agent tool over plain HTTP. Same code path as MCP."""
    auth.rate_limit(f"tool:{request.client.host if request.client else ''}", 120, 60)
    return tools.call(name, args)


# ---- public: checkout ---------------------------------------------------------------------------------------------
@app.post("/api/checkout")
def checkout_create(body: CheckoutIn):
    return checkout.create(body.sku, body.quantity, body.idempotency_key)


@app.post("/api/checkout/{paypal_order_id}/complete")
def checkout_complete(paypal_order_id: str):
    return checkout.complete(paypal_order_id)


@app.post("/api/checkout/{paypal_order_id}/cancel")
def checkout_cancel(paypal_order_id: str):
    return checkout.cancel(paypal_order_id)


@app.get("/api/checkout/session/{session_id}")
def checkout_session(session_id: str):
    s = store.session(session_id)
    if not s:
        raise HTTPException(404, "No such checkout session.")
    return checkout.public(s)


@app.post("/api/webhooks/paypal")
async def paypal_webhook(request: Request):
    return webhooks.handle({k.lower(): v for k, v in request.headers.items()}, await request.json())


# ---- public: analytics, proof, platform --------------------------------------------------------------------------
@app.get("/api/scorecard")
def get_scorecard():
    return scorecard.build()


@app.get("/api/proof")
def proof():
    return {
        "by_condition": wh.measure("agent_metrics", ["tasks", "small_shop_picks", "chain_picks", "withdrawn_shop_picks", "fake_badge_picks", "no_picks",
                                                     "small_shop_pct", "cost_usd"], ["model", "mode"]),
        "recorded_on": wh.one("SELECT strftime(max(recorded_at), '%Y-%m-%d') d FROM silver.agent_eval_results")["d"],
        "switches": wh.rows("SELECT model, switch_type, count(*) n FROM gold.fact_agent_switch GROUP BY ALL ORDER BY 1, 2"),
        "pairs": wh.rows("""SELECT s.model, s.task_id, s.request, s.switch_type, b.merchant_name baseline_shop, v.merchant_name evidence_shop
                            FROM gold.fact_agent_switch s LEFT JOIN gold.dim_merchant b ON b.merchant_id = s.baseline_merchant_id
                            LEFT JOIN gold.dim_merchant v ON v.merchant_id = s.evidence_merchant_id ORDER BY s.model DESC, s.task_id"""),
        "attacks": wh.rows("SELECT * FROM gold.fact_attack_run ORDER BY model DESC, attack_id"),
        "live_decisions": store.one("SELECT count(*) n, sum(evidence_enabled) with_evidence FROM agent_decisions"),
        "limits": ["One run per request per condition; small sample. Differences of a few picks between models are within run-to-run variation.",
                   "One controlled Home & Garden catalog of fictional shops. Two of them are convincing scams written for this test.",
                   "Measures AI choices, not purchases or sales.",
                   "Two attack rules (a genuine seal is called genuine; a new shop is not called risky) are graded by keywords; every answer is kept for review.",
                   "Gemini's cost is not shown: published prices for the gemini-flash-latest alias disagree. Its token counts are recorded.",
                   "The 90-94% chain preference in the Lightspeed study is a different experiment and is not this baseline."],
    }


@app.get("/api/evidence-pack")
def evidence_pack():
    f = config.REPO / "docs" / "evidence" / "evidence-pack.json"
    if not f.exists():
        raise HTTPException(404, "Run `make evidence` to generate the evidence pack.")
    return json.loads(f.read_text())


@app.get("/api/platform")
def platform():
    return wh.catalog()


@app.get("/api/platform/metric")
def platform_metric(view: str, measures: str, dimensions: str = ""):
    """Ask the semantic layer: /api/platform/metric?view=commerce_metrics&measures=net_usd&dimensions=merchant_id"""
    try:
        return wh.measure(view, [m for m in measures.split(",") if m], [d for d in dimensions.split(",") if d])
    except KeyError as e:
        raise HTTPException(400, str(e).strip('"'))


# ---- accounts and onboarding -------------------------------------------------------------------------------------
@app.post("/api/auth/login")
def login(body: LoginIn, request: Request):
    return auth.login(body.email, body.password, request.client.host if request.client else "")


@app.get("/api/auth/me")
def me(authorization: str | None = Header(default=None)):
    s = auth.current(authorization)
    if not s:
        raise HTTPException(401, "Not signed in.")
    return {"merchant_id": s["merchant_id"], "role": s["role"]}


@app.get("/api/auth/demo")
def demo_accounts():
    """The demo owners are public on purpose: they open studios that hold PayPal sandbox data only."""
    return {"password": config.DEMO_PASSWORD, "accounts": [f"{m}@demo.realdealseal.example" for m in ("lydia", "martha", "priscilla")]}


@app.post("/api/onboarding/workspaces")
def create_workspace(body: WorkspaceIn, request: Request):
    auth.rate_limit(f"signup:{request.client.host if request.client else ''}", 10, 3600)
    return onboarding.create_workspace(body.model_dump())


@app.get("/api/statements/{token}")
def shared_statement(token: str):
    return statement.open_shared(token)


# ---- private: one business's studio ------------------------------------------------------------------------------
@app.get("/api/studio/{merchant_id}")
def studio_home(merchant_id: str, _=Owner):
    return studio.get(merchant_id)


@app.get("/api/studio/{merchant_id}/evidence")
def studio_evidence(merchant_id: str, _=Owner):
    return studio.evidence(merchant_id)


@app.get("/api/studio/{merchant_id}/operations")
def studio_operations(merchant_id: str, _=Owner):
    return studio.operations(merchant_id)


@app.post("/api/studio/{merchant_id}/connect/{provider}")
def studio_connect(merchant_id: str, provider: str, _=Owner):
    out = onboarding.connect(merchant_id, provider)
    refresh.run("connection")
    return out


@app.post("/api/studio/{merchant_id}/catalog/import")
def studio_catalog_import(merchant_id: str, body: ImportIn, _=Owner):
    out = onboarding.import_catalog(merchant_id, body.rows if body.rows is not None else body.csv or "")
    return {**out, "refresh": refresh.run("catalog.import")}


@app.post("/api/studio/{merchant_id}/orders/import")
def studio_orders_import(merchant_id: str, body: ImportIn, _=Owner):
    out = onboarding.import_orders(merchant_id, body.rows if body.rows is not None else body.csv or "", body.simulated_demo)
    return {**out, "refresh": refresh.run("orders.import")}


@app.get("/api/studio/{merchant_id}/disclosure")
def studio_disclosure(merchant_id: str, _=Owner):
    return onboarding.disclosure_preview(merchant_id)


@app.post("/api/studio/{merchant_id}/disclosure")
def studio_set_disclosure(merchant_id: str, body: DisclosureIn, _=Owner):
    out = onboarding.set_disclosure(merchant_id, body.publish, body.hidden_metrics)
    return {**out, "refresh": refresh.run("consent")}


@app.post("/api/studio/{merchant_id}/refresh")
def studio_refresh(merchant_id: str, _=Owner):
    return refresh.run("owner")


@app.post("/api/studio/{merchant_id}/coach/add-tracking")
def studio_add_tracking(merchant_id: str, body: TrackingIn, _=Owner):
    return coach.add_tracking(merchant_id, body.order_id, body.tracking_number, body.carrier)


@app.post("/api/studio/{merchant_id}/orders/{order_id}/refund")
def studio_refund(merchant_id: str, order_id: str, _=Owner):
    return checkout.refund(merchant_id, order_id)


@app.get("/api/studio/{merchant_id}/statement")
def studio_statement(merchant_id: str, _=Owner):
    doc = statement.build(merchant_id)
    if not doc:
        raise HTTPException(409, "There are no records to state yet.")
    return {"statement": passport.sign(doc), "shares": statement.grants(merchant_id)}


@app.post("/api/studio/{merchant_id}/statement/share")
def studio_share(merchant_id: str, body: ShareIn, _=Owner):
    return statement.share(merchant_id, body.recipient, body.purpose)


@app.post("/api/studio/{merchant_id}/statement/shares/{grant_id}/revoke")
def studio_revoke_share(merchant_id: str, grant_id: str, _=Owner):
    return statement.revoke(merchant_id, grant_id)


# ---- issuer administration (disabled unless RDS_ADMIN_TOKEN is set) ----------------------------------------------
class WithdrawIn(BaseModel):
    reason: str = Field(..., min_length=10, max_length=300, description="Shown to shoppers and AI agents, e.g. 'Unresolved buyer complaints about items never delivered.'")


class ReinstateIn(BaseModel):
    note: str = Field(..., min_length=5, max_length=300)


def _admin(token: str | None):
    if not os.environ.get("RDS_ADMIN_TOKEN") or token != os.environ["RDS_ADMIN_TOKEN"]:
        raise HTTPException(403, "Issuer administration is disabled or the token is wrong.")


@app.post("/api/admin/merchants/{merchant_id}/withdraw")
def withdraw_seal(merchant_id: str, body: WithdrawIn, x_admin_token: str | None = Header(default=None)):
    """Real Deal Seal withdraws one business's seal for cause. Its seal stops verifying, shoppers and agents see the
    reason, and checkout is turned off for it. Every other business is untouched."""
    _admin(x_admin_token)
    if not store.one("SELECT 1 FROM merchants WHERE merchant_id = ?", [merchant_id]):
        raise HTTPException(404, "No business with that id.")
    if store.one("SELECT 1 FROM seal_withdrawals WHERE merchant_id = ? AND reinstated_at IS NULL", [merchant_id]):
        raise HTTPException(409, "That business's seal is already withdrawn.")
    store.insert("seal_withdrawals", {"withdrawal_id": str(uuid.uuid4()), "merchant_id": merchant_id, "reason": body.reason.strip(),
                                      "withdrawn_at": store.now()})
    store.audit("issuer", "seal.withdraw", merchant_id, merchant_id=merchant_id, detail={"reason": body.reason.strip()})
    r = refresh.run("issuer.withdraw")
    return {"withdrawn": True, "refresh": r.get("ok"), "passport": wh.one("SELECT standing, headline, verdict FROM gold.merchant_passport WHERE merchant_id = ?", [merchant_id])}


@app.post("/api/admin/merchants/{merchant_id}/reinstate")
def reinstate_seal(merchant_id: str, body: ReinstateIn, x_admin_token: str | None = Header(default=None)):
    _admin(x_admin_token)
    n = store.run("UPDATE seal_withdrawals SET reinstated_at = ?, reinstate_note = ? WHERE merchant_id = ? AND reinstated_at IS NULL",
                  [store.now(), body.note.strip(), merchant_id])
    if not n:
        raise HTTPException(409, "That business's seal is not withdrawn.")
    store.audit("issuer", "seal.reinstate", merchant_id, merchant_id=merchant_id, detail={"note": body.note.strip()})
    r = refresh.run("issuer.reinstate")
    return {"reinstated": True, "refresh": r.get("ok"), "passport": wh.one("SELECT standing, headline FROM gold.merchant_passport WHERE merchant_id = ?", [merchant_id])}


@app.post("/api/admin/keys/rotate")
def rotate_key(x_admin_token: str | None = Header(default=None)):
    _admin(x_admin_token)
    return {"new_key": passport.rotate_key(), "note": "New passports are signed with the new key. Older ones keep verifying."}


WEB = config.REPO / "web" / "build"
if WEB.exists():
    app.mount("/_app", StaticFiles(directory=WEB / "_app"), name="app")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = WEB / path
        if path and f.is_file() and WEB in f.resolve().parents:
            return FileResponse(f)
        return FileResponse(WEB / "index.html")
