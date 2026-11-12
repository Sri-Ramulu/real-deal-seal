"""Onboard the two sample businesses through the public API, exactly as a new owner would. No code changes.

    python scripts/seed_samples.py [http://localhost:8000]
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def call(path, body=None, token=None):
    req = urllib.request.Request(BASE + path, method="POST" if body is not None else "GET", data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: {e.code} {e.read().decode()[:300]}")


for name, btype, category, sells, slug in [
        ("Bright Clean Co.", "services", "Home services", "Home cleaning in Salt Lake City", "bright-clean"),
        ("Pixel Press Studio", "digital", "Digital products", "Editable templates for small businesses", "pixel-press")]:
    ws = call("/api/onboarding/workspaces", {"name": name, "business_type": btype, "category": category, "region": "US", "sells": sells,
                                             "ships_from": "Salt Lake City, UT" if btype == "services" else "Instant download",
                                             "returns_policy": "Free reschedule up to 24 hours before" if btype == "services" else "Refund within 14 days if not downloaded",
                                             "email": f"owner@{slug}.example", "password": "sample-owner-1"})
    mid, tok = ws["merchant_id"], ws["token"]
    call(f"/api/studio/{mid}/connect/records_import", {}, tok)
    cat = call(f"/api/studio/{mid}/catalog/import", {"csv": (SAMPLES / f"{slug}.catalog.csv").read_text()}, tok)
    imp = call(f"/api/studio/{mid}/orders/import", {"csv": (SAMPLES / f"{slug}.orders.csv").read_text(), "simulated_demo": True}, tok)
    call(f"/api/studio/{mid}/disclosure", {"publish": True, "hidden_metrics": []}, tok)
    p = call(f"/api/merchants/{mid}")["passport"]
    print(f"{name}: {cat['accepted']} catalog items, {imp['accepted']} orders accepted, {len(imp['rejected'])} rejected -> {p['headline']} ({p['rules_met']} of {p['rules_total']} rules)")
