"""The semantic layer: a number has one definition.

Each domain's semantic.yaml declares metric views (a gold table, its dimensions and its measures).
`compile_query` turns a request for measures by dimensions into SQL; nobody re-types a formula.
"""
from __future__ import annotations

import yaml

from . import DOMAINS


def views() -> dict[str, dict]:
    out = {}
    for f in sorted(DOMAINS.glob("*/semantic.yaml")):
        for v in yaml.safe_load(f.read_text())["metric_views"]:
            out[v["name"]] = {**v, "domain": f.parent.name}
    return out


def compile_query(view: str, measures: list[str], dimensions: list[str] | None = None,
                  where: dict | None = None) -> tuple[str, list]:
    v = views()[view]
    dims = {d["name"]: d for d in v.get("dimensions", [])}
    meas = {m["name"]: m for m in v["measures"]}
    dimensions = dimensions or []
    for d in dimensions:
        if d not in dims:
            raise KeyError(f"{view} has no dimension '{d}'")
    for m in measures:
        if m not in meas:
            raise KeyError(f"{view} has no measure '{m}'. Add it to semantic.yaml; do not hand-write the formula.")
    cols = [f"{dims[d]['expr']} AS {d}" for d in dimensions] + [f"{meas[m]['expr']} AS {m}" for m in measures]
    sql = f"SELECT {', '.join(cols)} FROM {v['source']}"
    params, conds = [], [v["filter"]] if v.get("filter") else []
    for k, val in (where or {}).items():
        if k not in dims:
            raise KeyError(f"{view} has no dimension '{k}' to filter on")
        conds.append(f"{dims[k]['expr']} = ?")
        params.append(val)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    if dimensions:
        sql += " GROUP BY " + ", ".join(str(i + 1) for i in range(len(dimensions))) + " ORDER BY 1"
    return sql, params


def query(con, view: str, measures: list[str], dimensions: list[str] | None = None, where: dict | None = None) -> list[dict]:
    sql, params = compile_query(view, measures, dimensions, where)
    cur = con.execute(sql, params)
    names = [c[0] for c in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]
