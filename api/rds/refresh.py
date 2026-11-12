"""Refresh: operational store -> extract -> pipeline -> credentials.

Runs after anything that changes evidence (an import, a captured payment, a refund, a tracking record, a consent
change). It is a job with retries: if the pipeline goes red the last good warehouse keeps serving and the job
records why. Running it twice with nothing changed issues nothing new.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import config, passport, store, warehouse

EXTRACT = Path(config.os.environ["RDS_EXTRACT_DIR"]) / "ops"


def _write(name: str, rows: list[dict]) -> str:
    EXTRACT.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    (EXTRACT / f"{name}.jsonl").write_text(text)
    return hashlib.sha256(text.encode()).hexdigest()


def _withdrawal(m: dict) -> dict:
    """Why a seal is withdrawn, if it is. Real Deal Seal's own withdrawal for cause wins; otherwise a business that took
    its published passport down is recorded as withdrawn by the business, so it never looks like an unknown shop."""
    w = store.one("SELECT reason, withdrawn_at FROM seal_withdrawals WHERE merchant_id = ? AND reinstated_at IS NULL ORDER BY withdrawn_at DESC LIMIT 1",
                  [m["merchant_id"]])
    if w:
        return {"seal_withdrawn_by": "issuer", "seal_withdrawn_at": w["withdrawn_at"], "seal_withdrawn_reason": w["reason"]}
    if not m["passport_published"]:
        g = store.one("SELECT revoked_at FROM consent_grants WHERE merchant_id = ? AND purpose = 'public_passport' ORDER BY granted_at DESC LIMIT 1",
                      [m["merchant_id"]])
        if (g and g["revoked_at"]) or (not g and m["origin"] == "demo"):
            return {"seal_withdrawn_by": "business", "seal_withdrawn_at": g["revoked_at"] if g else None,
                    "seal_withdrawn_reason": "The business withdrew its public passport."}
    return {"seal_withdrawn_by": None, "seal_withdrawn_at": None, "seal_withdrawn_reason": None}


def export() -> dict:
    """Snapshot the tenant-owned source tables. Simulated checkouts are never exported: a simulated payment is not evidence."""
    merchants = []
    for m in store.q("SELECT * FROM merchants ORDER BY merchant_id"):
        withdrawal = _withdrawal(m)
        conn = store.one("SELECT provider, status FROM merchant_connections WHERE merchant_id = ? ORDER BY (provider = 'paypal') DESC, created_at LIMIT 1", [m["merchant_id"]])
        merchants.append({"merchant_id": m["merchant_id"], "origin": m["origin"], "name": m["name"], "business_type": m["business_type"], "category": m["category"],
                          "region": m["region"], "sells": m["sells"], "ships_from": m["ships_from"], "returns": m["returns_policy"],
                          "passport_published": bool(m["passport_published"]), "hidden_metrics": json.loads(m["hidden_metrics"]),
                          "connection_provider": conn["provider"] if conn else "none", "connection_status": conn["status"] if conn else "none",
                          **withdrawal})
    # Demo shops are exported too, but the pipeline takes only their disclosure choices from here; their identity stays in landing.
    orders = store.q("SELECT * FROM orders WHERE source_system <> 'simulated_checkout' ORDER BY merchant_id, seq")
    skip = {r["order_id"] for r in store.q("SELECT order_id FROM orders WHERE source_system = 'simulated_checkout'")}
    pay = [e for e in store.q("SELECT * FROM payment_events ORDER BY recorded_at, event_id") if e["order_id"] not in skip]
    ful = [e for e in store.q("SELECT * FROM fulfillment_events ORDER BY recorded_at, event_id") if e["order_id"] not in skip]
    items = [{**i, "tags": json.loads(i["tags"])} for i in store.q("SELECT * FROM catalog_items ORDER BY sku")]
    return {"merchants": _write("merchants", merchants),
            "orders": _write("orders", [{**o, "simulated": bool(o["simulated"])} for o in orders]),
            "payment_events": _write("payment_events", pay), "fulfillment_events": _write("fulfillment_events", ful),
            "catalog_items": _write("catalog_items", items)}


def _code_fingerprint() -> str:
    """A hash of everything a build reads from the image: the domains' SQL, contracts and semantic layer, the
    pipeline code and the landing files (catalog, PayPal readbacks, the recorded evaluation)."""
    import hashlib
    from .config import REPO
    h = hashlib.sha256()
    base = REPO / "data_platform"
    for sub_ in ("domains", "landing", "rdsp", "run"):
        for f in sorted((base / sub_).rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                h.update(str(f.relative_to(base)).encode())
                h.update(f.read_bytes())
    return h.hexdigest()


def _fingerprint_file():
    return warehouse.warehouse_path().parent / "build.fingerprint"


def stale() -> bool:
    """True when the warehouse on disk was built from older pipeline code or landing data, as after a deploy."""
    f = _fingerprint_file()
    return not f.exists() or f.read_text().strip() != _code_fingerprint()


@store.unscoped
def run(reason: str = "manual", attempts: int = 2) -> dict:
    job = {"kind": f"refresh:{reason}", "status": "running", "created_at": store.now(), "updated_at": store.now()}
    store.insert("jobs", job)
    job_id = store.one("SELECT max(job_id) id FROM jobs")["id"]
    error = None
    for attempt in range(1, attempts + 1):
        try:
            hashes = export()
            warehouse.rebuild()
            issued = reconcile_credentials()
            _fingerprint_file().write_text(_code_fingerprint())
            store.run("UPDATE jobs SET status = 'done', attempts = ?, updated_at = ? WHERE job_id = ?", [attempt, store.now(), job_id])
            return {"ok": True, "job_id": job_id, "extract": hashes, "credentials": issued, "pipeline_run": warehouse.catalog()["run_id"]}
        except Exception as e:  # a red gate or a transient failure: keep the last good warehouse and report
            error = f"{type(e).__name__}: {e}"
            store.run("UPDATE jobs SET attempts = ?, last_error = ?, updated_at = ? WHERE job_id = ?", [attempt, error[:500], store.now(), job_id])
    store.run("UPDATE jobs SET status = 'failed', updated_at = ? WHERE job_id = ?", [store.now(), job_id])
    store.audit("refresh", "pipeline.refresh", result="failed", detail={"error": error, "reason": reason})
    return {"ok": False, "job_id": job_id, "error": error}


@store.unscoped
def reconcile_credentials() -> dict:
    """Make the credential registry match gold: issue when facts changed, supersede the old one, revoke when unpublished."""
    out = {"issued": 0, "superseded": 0, "revoked": 0, "unchanged": 0}
    for p in warehouse.rows("""SELECT merchant_id, has_record, passport_published, standing, verdict FROM gold.merchant_passport
                               WHERE merchant_kind = 'paypal_merchant'"""):
        active = store.one("SELECT * FROM credentials WHERE merchant_id = ? AND kind = 'passport' AND status = 'active'", [p["merchant_id"]])
        if not (p["has_record"] and p["passport_published"]) or p["standing"] == "withdrawn":
            if active:
                passport.set_status(active["credential_id"], "revoked",
                                    p["verdict"] if p["standing"] == "withdrawn" else "The business withdrew its public passport.")
                out["revoked"] += 1
            continue
        cred = passport.issue(p["merchant_id"])
        if active and cred and cred["id"] == active["credential_id"]:
            out["unchanged"] += 1
            continue
        out["superseded"] += bool(active)
        out["issued"] += 1
    return out
