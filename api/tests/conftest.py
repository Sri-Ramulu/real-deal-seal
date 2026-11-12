import os
import sys
import tempfile
from pathlib import Path

os.environ["RDS_REFRESH_HOURS"] = "0"
os.environ["RDS_DEMO_SHOPS"] = "0"  # tests that need the demo shops create them explicitly
os.environ["RDS_NO_DOTENV"] = "1"
os.environ["RDS_VAR_DIR"] = tempfile.mkdtemp(prefix="rds-test-")
for _k in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
    os.environ.pop(_k, None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from rds.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def owner(client):
    """Bearer headers for a demo owner: owner("martha")."""
    tokens = {}  # one login per shop: the login route is rate limited, as it should be

    def login(shop):
        if shop not in tokens or client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens[shop]}"}).status_code != 200:
            tokens[shop] = client.post("/api/auth/login", json={"email": f"{shop}@demo.realdealseal.example", "password": "demo-owner"}).json()["token"]
        return {"Authorization": f"Bearer {tokens[shop]}"}
    return login
