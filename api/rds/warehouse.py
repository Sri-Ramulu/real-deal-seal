"""Read-only access to the warehouse. The API never writes to gold; only the pipeline does (see refresh.py)."""
from __future__ import annotations

import datetime
import decimal
import json
import sys
import threading

import duckdb

from .config import REPO

sys.path.insert(0, str(REPO / "data_platform"))
from rdsp import catalog_path, runner, semantic, warehouse_path  # noqa: E402

_lock = threading.RLock()
_con = None


def _safe(v):
    if isinstance(v, decimal.Decimal):
        return float(v) if v % 1 else int(v)
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    if isinstance(v, (list, tuple)):
        return [_safe(x) for x in v]
    return v


def con():
    global _con
    with _lock:
        if _con is None:
            if not warehouse_path().exists() or not catalog_path().exists():
                runner.build(quiet=True)
            _con = duckdb.connect(str(warehouse_path()), read_only=True)
        return _con


def rebuild():
    """Build a new warehouse beside the live one and swap it in only if all four gates pass.
    A red gate raises and the API keeps serving the last good build."""
    global _con
    tmp_w = warehouse_path().with_suffix(".next.duckdb")
    tmp_c = catalog_path().with_suffix(".next.json")
    runner.build(path=tmp_w, quiet=True, catalog_out=tmp_c)
    with _lock:
        if _con is not None:
            _con.close()
            _con = None
        tmp_w.replace(warehouse_path())
        tmp_c.replace(catalog_path())
        con()


def rows(sql: str, params: list | None = None) -> list[dict]:
    with _lock:
        cur = con().cursor()
        try:
            cur.execute(sql, params or [])
            names = [c[0] for c in cur.description]
            return [{n: _safe(v) for n, v in zip(names, r)} for r in cur.fetchall()]
        finally:
            cur.close()


def one(sql: str, params: list | None = None) -> dict | None:
    r = rows(sql, params)
    return r[0] if r else None


def measure(view: str, measures: list[str], dimensions: list[str] | None = None, where: dict | None = None) -> list[dict]:
    """Ask the semantic layer. Formulas live in the domains' semantic.yaml, not here."""
    sql, params = semantic.compile_query(view, measures, dimensions, where)
    return rows(sql, params)


def catalog() -> dict:
    con()
    return json.loads(catalog_path().read_text())
