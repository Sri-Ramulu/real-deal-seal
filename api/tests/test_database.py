"""The operational database: schema version, and on PostgreSQL, row-level security between businesses."""
import pytest

from rds import store


def test_deep_health_reports_a_current_schema(client):
    h = client.get("/api/health/deep").json()
    assert h["ok"] and h["schema_current"] and h["backend"] == store.BACKEND
    assert "003_status_list.sql" in h["migrations_applied"]


@pytest.mark.skipif(store.BACKEND != "postgres", reason="row-level security is a PostgreSQL feature")
def test_row_level_security_walls_each_business_off(client):
    h = store.health()
    assert h["row_level_security"] and all(h["row_level_security"].values()), h["row_level_security"]
    everyone = {r["merchant_id"] for r in store.q("SELECT merchant_id FROM merchants")}
    assert {"lydia", "martha"} <= everyone
    with store.tenant("martha"):
        seen = {r["merchant_id"] for r in store.q("SELECT merchant_id FROM merchants")}
        assert seen == {"martha"}, "a query with no filter still sees only its own business"
        assert store.q("SELECT * FROM credentials WHERE merchant_id = 'lydia'") == []
        assert store.run("UPDATE merchants SET name = 'hijacked' WHERE merchant_id = 'lydia'") == 0
        with pytest.raises(Exception):
            store.insert("seal_withdrawals", {"withdrawal_id": "x", "merchant_id": "lydia", "reason": "not mine to write", "withdrawn_at": store.now()})
    assert store.one("SELECT name FROM merchants WHERE merchant_id = 'lydia'")["name"] != "hijacked"


@pytest.mark.skipif(store.BACKEND != "postgres", reason="row-level security is a PostgreSQL feature")
def test_a_studio_request_is_scoped_to_its_business(client, owner):
    r = client.get("/api/studio/martha/evidence", headers=owner("martha"))
    assert r.status_code == 200
    assert client.get("/api/studio/lydia", headers=owner("martha")).status_code in (401, 403)
