"""Bronze: every delivered row, kept as text. Nothing is cleaned or dropped here."""
from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path

import yaml

from . import DOMAINS, ROOT, extract_dir


def _rows(doc, fmt: str, key: str | None):
    """Yield (map_key, row, file_meta) for one parsed landing file."""
    if fmt == "jsonl":
        for row in doc:
            yield None, row, {}
        return
    meta = {k: v for k, v in doc.items() if not isinstance(v, (list, dict))} if isinstance(doc, dict) else {}
    body = doc[key] if key else doc
    if fmt == "json_key_array":
        for row in body:
            yield None, row if isinstance(row, dict) else {"value": row}, meta
    elif fmt == "json_key_map":
        for k, row in body.items():
            yield k, row, meta
    else:
        raise ValueError(f"unknown format {fmt}")


def sources() -> list[dict]:
    out = []
    for f in sorted(DOMAINS.glob("*/sources.yaml")):
        for s in yaml.safe_load(f.read_text())["sources"]:
            out.append({**s, "domain": f.parent.name})
    return out


def load(con, loaded_at: str) -> list[dict]:
    """Load every declared source. Returns one manifest entry per file (gate 1 and 2 read it)."""
    con.execute("CREATE SCHEMA IF NOT EXISTS bronze")
    manifest = []
    for s in sources():
        table = f"bronze.{s['table']}"
        con.execute(f"""CREATE OR REPLACE TABLE {table} (_source_file VARCHAR, _sha256 VARCHAR, _loaded_at TIMESTAMP,
                        _row_no INTEGER, _key VARCHAR, file_meta JSON, payload JSON)""")
        # "extract/..." sources come from the operational store's extract; everything else from landing.
        from_extract = s["files"].startswith("extract/")
        base = extract_dir() if from_extract else ROOT
        files = sorted(glob.glob(str(base / (s["files"][len("extract/"):] if from_extract else s["files"]))))
        for path in files:
            raw = Path(path).read_bytes()
            rel = ("extract/" if from_extract else "") + str(Path(path).relative_to(base))
            sha = hashlib.sha256(raw).hexdigest()
            text = raw.decode("utf-8")
            doc = [json.loads(line) for line in text.splitlines() if line.strip()] if s["format"] == "jsonl" else json.loads(text)
            rows = [(rel, sha, loaded_at, i, k, json.dumps(meta), json.dumps(row))
                    for i, (k, row, meta) in enumerate(_rows(doc, s["format"], s.get("key")), start=1)]
            if rows:
                con.executemany(f"INSERT INTO {table} VALUES (?,?,?,?,?,?,?)", rows)
            manifest.append({"domain": s["domain"], "table": table, "file": rel,
                             "sha256": sha, "rows_delivered": len(rows)})
        if not files and not s.get("optional"):
            manifest.append({"domain": s["domain"], "table": table, "file": s["files"], "sha256": None, "rows_delivered": 0})
    return manifest
