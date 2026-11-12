"""A small Python client for the Real Deal Seal API. Standard library only.

    from realdealseal import Client
    rds = Client("http://localhost:8000")
    offers = rds.search_products("purple table runner")
    passport = rds.passport("lydia")
    print(rds.verify(passport["seal"])["result"])          # genuine
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"{status}: {message}")
        self.status, self.message = status, message


class Client:
    def __init__(self, base_url: str = "http://localhost:8000", token: str | None = None, transport=None):
        self.base_url, self.token = base_url.rstrip("/"), token
        self._transport = transport or self._http

    def _http(self, method: str, path: str, body):
        req = urllib.request.Request(self.base_url + path, method=method, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {self.token}"} if self.token else {})})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def _call(self, method: str, path: str, body=None):
        status, data = self._transport(method, path, body)
        if status >= 400:
            raise ApiError(status, (data or {}).get("message") or (data or {}).get("detail") or "request failed")
        return data

    # ---- public: evidence ----
    def merchants(self) -> list[dict]:
        return self._call("GET", "/api/merchants")

    def passport(self, merchant_id: str) -> dict:
        return self._call("GET", f"/api/merchants/{merchant_id}")

    def verify(self, credential: dict | str) -> dict:
        return self._call("POST", "/api/verify", {"credential": credential})

    def criteria(self) -> dict:
        return self._call("GET", "/api/criteria")

    def metric(self, view: str, measures: list[str], dimensions: list[str] | None = None) -> list[dict]:
        q = urllib.parse.urlencode({"view": view, "measures": ",".join(measures), "dimensions": ",".join(dimensions or [])})
        return self._call("GET", f"/api/platform/metric?{q}")

    # ---- public: agent tools (same code path as MCP) ----
    def tool(self, name: str, **args) -> dict:
        return self._call("POST", f"/api/tools/{name}", args)

    def search_products(self, query: str, max_price_usd: float | None = None) -> list[dict]:
        return self.tool("search_products", query=query, **({"max_price_usd": max_price_usd} if max_price_usd else {}))["offers"]

    # ---- public: checkout ----
    def create_checkout(self, sku: str, quantity: int = 1, idempotency_key: str | None = None) -> dict:
        return self._call("POST", "/api/checkout", {"sku": sku, "quantity": quantity, "idempotency_key": idempotency_key})

    # ---- private: one business ----
    def login(self, email: str, password: str) -> "Client":
        self.token = self._call("POST", "/api/auth/login", {"email": email, "password": password})["token"]
        return self

    def studio(self, merchant_id: str) -> dict:
        return self._call("GET", f"/api/studio/{merchant_id}")

    def import_orders(self, merchant_id: str, rows: list[dict]) -> dict:
        return self._call("POST", f"/api/studio/{merchant_id}/orders/import", {"rows": rows})
