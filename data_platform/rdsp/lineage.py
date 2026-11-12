"""Lineage is read from the SQL headers, never drawn by hand.

Every model starts with `-- writes: schema.table`, `-- reads: a, b` and optionally `-- key: col`.
"""
from __future__ import annotations

import re
from graphlib import TopologicalSorter
from pathlib import Path

from . import DOMAINS

HEADER = re.compile(r"^--\s*(writes|reads|key|grain):\s*(.+)$", re.M)


def models() -> list[dict]:
    out = []
    for f in sorted(DOMAINS.glob("*/*/*.sql")):
        text = f.read_text()
        h = {k: v.strip() for k, v in HEADER.findall(text)}
        if "writes" not in h:
            raise ValueError(f"{f} has no '-- writes:' header")
        out.append({"file": str(f.relative_to(DOMAINS.parent)), "domain": f.parts[-3], "layer": f.parts[-2],
                    "writes": h["writes"], "reads": [r.strip() for r in h.get("reads", "").split(",") if r.strip()],
                    "key": [k.strip() for k in h.get("key", "").split(",") if k.strip()],
                    "grain": h.get("grain"), "sql": text})
    return out


def ordered(ms: list[dict]) -> list[dict]:
    by = {m["writes"]: m for m in ms}
    ts = TopologicalSorter({m["writes"]: [r for r in m["reads"] if r in by] for m in ms})
    return [by[t] for t in ts.static_order()]


def graph(ms: list[dict], bronze_tables: list[dict]) -> dict:
    nodes, edges = {}, []
    for b in bronze_tables:
        nodes[b["file"]] = {"id": b["file"], "layer": "landing", "domain": b["domain"]}
        nodes[b["table"]] = {"id": b["table"], "layer": "bronze", "domain": b["domain"]}
        edges.append({"from": b["file"], "to": b["table"]})
    for m in ms:
        nodes[m["writes"]] = {"id": m["writes"], "layer": m["layer"], "domain": m["domain"], "file": m["file"]}
        edges += [{"from": r, "to": m["writes"]} for r in m["reads"]]
    return {"nodes": list(nodes.values()), "edges": edges}


def upstream(g: dict, table: str) -> list[str]:
    parents = {}
    for e in g["edges"]:
        parents.setdefault(e["to"], []).append(e["from"])
    seen, stack = [], [table]
    while stack:
        for p in parents.get(stack.pop(), []):
            if p not in seen:
                seen.append(p)
                stack.append(p)
    return seen
