import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdsp import runner  # noqa: E402


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    path = tmp_path_factory.mktemp("wh") / "rds.duckdb"
    catalog = runner.build(path, quiet=True)
    return path, catalog


@pytest.fixture()
def con(built):
    c = duckdb.connect(str(built[0]), read_only=True)
    yield c
    c.close()


@pytest.fixture()
def catalog(built):
    return built[1]
