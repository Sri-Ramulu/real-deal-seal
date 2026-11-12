"""The build: landing -> bronze -> silver -> gold, with four gates. The gates decide, not the author.

Gate 1  landing    every declared source file is present and hashed
Gate 2  bronze     rows loaded = rows delivered, for every file
Gate 3  keys       every model's declared key is unique and never null
Gate 4  contracts  every rule of every data contract holds
"""
from __future__ import annotations

import datetime
import json
import sys

import duckdb
import yaml

from . import DOMAINS, bronze, catalog_path, contracts, lineage, semantic, warehouse_path


class GateFailed(Exception):
    pass


def _gate(con, run_id, n, name, failures, checked):
    con.execute("INSERT INTO ops.gate_results VALUES (?,?,?,?,?,?)",
                [run_id, n, name, checked, len(failures), json.dumps(failures[:20])])
    if failures:
        raise GateFailed(f"gate {n} ({name}) failed: {failures[:5]}")


def build(path=None, quiet=False, catalog_out=None) -> dict:
    path = path or warehouse_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = duckdb.connect(str(path))
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0, tzinfo=None)
    run_id = now.strftime("%Y%m%dT%H%M%SZ")
    say = (lambda *a: None) if quiet else print
    for s in ("ops", "bronze", "silver", "gold"):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {s}")
    con.execute("CREATE TABLE ops.gate_results (run_id VARCHAR, gate INTEGER, name VARCHAR, checked INTEGER, failed INTEGER, failures JSON)")
    con.execute("CREATE TABLE ops.contract_results (run_id VARCHAR, product VARCHAR, version VARCHAR, table_name VARCHAR, rule VARCHAR, passed BOOLEAN, detail VARCHAR)")
    con.execute("CREATE TABLE ops.model_runs (run_id VARCHAR, model VARCHAR, layer VARCHAR, domain VARCHAR, row_count BIGINT)")

    manifest = bronze.load(con, now.isoformat(sep=" "))
    _gate(con, run_id, 1, "landing", [m["file"] for m in manifest if m["sha256"] is None], len(manifest))
    bad = []
    for m in manifest:
        got = con.execute(f"SELECT count(*) FROM {m['table']} WHERE _source_file = ?", [m["file"]]).fetchone()[0]
        if got != m["rows_delivered"]:
            bad.append(f"{m['file']}: delivered {m['rows_delivered']}, loaded {got}")
    _gate(con, run_id, 2, "bronze", bad, len(manifest))
    say(f"bronze   {len(manifest)} files, {sum(m['rows_delivered'] for m in manifest)} rows")

    ms = lineage.ordered(lineage.models())
    key_failures, keys_checked = [], 0
    for m in ms:
        body = "\n".join(l for l in m["sql"].splitlines() if not l.startswith("--"))
        con.execute(f"CREATE OR REPLACE TABLE {m['writes']} AS {body}")
        n = con.execute(f"SELECT count(*) FROM {m['writes']}").fetchone()[0]
        con.execute("INSERT INTO ops.model_runs VALUES (?,?,?,?,?)", [run_id, m["writes"], m["layer"], m["domain"], n])
        if m["key"]:
            keys_checked += 1
            k = ", ".join(m["key"])
            dup = con.execute(f"SELECT count(*) FROM (SELECT {k} FROM {m['writes']} GROUP BY ALL HAVING count(*) > 1)").fetchone()[0]
            nul = con.execute(f"SELECT count(*) FROM {m['writes']} WHERE " + " OR ".join(f"{c} IS NULL" for c in m["key"])).fetchone()[0]
            if dup or nul:
                key_failures.append(f"{m['writes']} key ({k}): {dup} duplicates, {nul} nulls")
        say(f"{m['layer']:<8} {m['writes']:<34} {n:>5} rows")
    _gate(con, run_id, 3, "keys", key_failures, keys_checked)

    results = contracts.check(con)
    con.executemany("INSERT INTO ops.contract_results VALUES (?,?,?,?,?,?,?)",
                    [(run_id, r["product"], r["version"], r["table"], r["rule"], r["passed"], r["detail"]) for r in results])
    _gate(con, run_id, 4, "contracts", [f"{r['table']}: {r['rule']} ({r['detail']})" for r in results if not r["passed"]], len(results))
    say(f"contracts {len(results)} rules checked, all passed")

    catalog = publish(con, run_id, manifest, ms, results, catalog_out or catalog_path())
    con.close()
    return catalog


def publish(con, run_id, manifest, ms, results, out) -> dict:
    """The marketplace catalog: products, tables, columns, lineage, contracts, metrics. Read by the API."""
    products = []
    for f in sorted(DOMAINS.glob("*/product.yaml")):
        products.append({**yaml.safe_load(f.read_text()), "domain": f.parent.name})
    meta = {}
    for f in sorted(DOMAINS.glob("*/metadata.yaml")):
        for t in yaml.safe_load(f.read_text())["tables"]:
            meta[t["name"]] = {**t, "domain": f.parent.name}
    tables = []
    for m in ms:
        cols = [{"name": r[0], "type": r[1]} for r in con.execute(f"DESCRIBE {m['writes']}").fetchall()]
        doc = meta.get(m["writes"], {})
        cdoc = {c["name"]: c for c in doc.get("columns", [])}
        for c in cols:
            c.update({k: v for k, v in cdoc.get(c["name"], {}).items() if k != "name"})
        tables.append({"name": m["writes"], "layer": m["layer"], "domain": m["domain"], "file": m["file"], "key": m["key"],
                       "grain": m["grain"], "description": doc.get("description"), "owner": doc.get("owner"),
                       "rows": con.execute(f"SELECT count(*) FROM {m['writes']}").fetchone()[0], "columns": cols})
    g = lineage.graph(ms, manifest)
    catalog = {
        "run_id": run_id,
        "products": products,
        "tables": tables,
        "lineage": g,
        "sources": manifest,
        "gates": [dict(zip(["gate", "name", "checked", "failed"], r)) for r in
                  con.execute("SELECT gate, name, checked, failed FROM ops.gate_results ORDER BY gate").fetchall()],
        "contracts": [{"name": c["name"], "version": c["version"], "status": c["status"], "domain": c["_domain"],
                       "description": c["description"]["purpose"], "sla": c.get("slaProperties", []),
                       "rules": [r for r in results if r["product"] == c["name"]]} for c in contracts.all_contracts()],
        "metric_views": list(semantic.views().values()),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalog, indent=1, default=str))
    return catalog


if __name__ == "__main__":
    try:
        build()
    except GateFailed as e:
        print("RED:", e, file=sys.stderr)
        sys.exit(1)
