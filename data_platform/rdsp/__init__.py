"""Real Deal Seal data platform: the shared, self-serve part of the mesh.

Domains own their SQL, metadata, contract and metrics. This package only knows how to
load landing files, run SQL in dependency order, check gates and publish the catalog.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ROOT / "domains"
LANDING = ROOT / "landing"
WAREHOUSE = ROOT / "warehouse" / "rds.duckdb"
CATALOG = ROOT / "build" / "catalog.json"


def extract_dir() -> Path:
    """Where the operational store writes its extract (orders, events, merchants created at runtime)."""
    return Path(os.environ.get("RDS_EXTRACT_DIR", ROOT / "extract"))


def warehouse_path() -> Path:
    return Path(os.environ.get("RDS_WAREHOUSE", WAREHOUSE))


def catalog_path() -> Path:
    return Path(os.environ.get("RDS_CATALOG", CATALOG))
