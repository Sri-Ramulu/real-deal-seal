"""Data contracts (Open Data Contract Standard layout): what consumers can rely on.

A contract lists the tables of a data product, their columns and the quality rules that must hold.
`check` runs every rule against the warehouse and returns one result row per rule.
"""
from __future__ import annotations

import yaml

from . import DOMAINS


def all_contracts() -> list[dict]:
    return [{**yaml.safe_load(f.read_text()), "_domain": f.parent.name} for f in sorted(DOMAINS.glob("*/contract.odcs.yaml"))]


def _scalar(con, sql: str):
    return con.execute(sql).fetchone()[0]


def check(con) -> list[dict]:
    results = []

    def add(c, table, rule, ok, detail):
        results.append({"product": c["name"], "version": c["version"], "table": table, "rule": rule,
                        "passed": bool(ok), "detail": str(detail)})

    for c in all_contracts():
        for t in c["schema"]:
            table = t["physicalName"]
            actual = {r[0]: r[1] for r in con.execute(f"DESCRIBE {table}").fetchall()}
            for p in t["properties"]:
                col = p["name"]
                add(c, table, f"column {col} exists", col in actual, actual.get(col, "missing"))
                if col not in actual:
                    continue
                if p.get("physicalType"):
                    add(c, table, f"{col} is {p['physicalType']}", actual[col].upper().startswith(p["physicalType"].upper()), actual[col])
                if p.get("required"):
                    n = _scalar(con, f'SELECT count(*) FROM {table} WHERE "{col}" IS NULL')
                    add(c, table, f"{col} is never null", n == 0, f"{n} nulls")
                if p.get("unique"):
                    n = _scalar(con, f'SELECT count(*) - count(DISTINCT "{col}") FROM {table}')
                    add(c, table, f"{col} is unique", n == 0, f"{n} duplicates")
                if p.get("acceptedValues"):
                    vals = ", ".join("'" + v.replace("'", "''") + "'" for v in p["acceptedValues"])
                    n = _scalar(con, f'SELECT count(*) FROM {table} WHERE "{col}" IS NOT NULL AND CAST("{col}" AS VARCHAR) NOT IN ({vals})')
                    add(c, table, f"{col} in accepted values", n == 0, f"{n} outside the list")
            for q in t.get("quality", []):
                got = _scalar(con, q["query"])
                add(c, table, q["name"], got == q["mustBe"], f"got {got}, must be {q['mustBe']}")
    return results
