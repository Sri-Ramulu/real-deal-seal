"""The published client works against the API with no knowledge of its internals."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sdk" / "python"))
from realdealseal import ApiError, Client  # noqa: E402


@pytest.fixture()
def rds(client):
    def transport(method, path, body):
        r = client.request(method, path, json=body, headers={"Authorization": f"Bearer {sdk.token}"} if sdk.token else {})
        return r.status_code, r.json()
    sdk = Client("http://testserver", transport=transport)
    return sdk


def test_an_external_developer_can_search_read_and_verify(rds):
    offers = rds.search_products("purple table runner")
    assert offers and {"sku", "shop", "shop_standing", "seller_text"} <= set(offers[0])
    p = rds.passport("lydia")
    assert rds.verify(p["seal"])["genuine"]
    assert rds.metric("commerce_metrics", ["orders"], ["merchant_id"])


def test_the_client_surfaces_api_errors_as_messages(rds):
    with pytest.raises(ApiError) as e:
        rds.passport("nobody")
    assert e.value.status == 404 and "cannot vouch" in e.value.message
    with pytest.raises(ApiError) as e:
        rds.studio("lydia")
    assert e.value.status == 401


def test_the_openapi_contract_lists_the_public_and_private_routes(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/api/merchants/{merchant_id}", "/api/verify", "/api/checkout", "/api/studio/{merchant_id}/orders/import", "/api/webhooks/paypal"} <= set(paths)
