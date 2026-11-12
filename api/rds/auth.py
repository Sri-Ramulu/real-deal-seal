"""Merchant accounts, sessions and tenant isolation.

Every private route goes through `require_merchant`, which checks that the caller's session belongs to the
merchant in the URL. A wrong-tenant attempt is refused and written to the audit trail.
"""
from __future__ import annotations

import datetime
import hashlib
import hmac
import os
import secrets
import time
import uuid

from fastapi import Header, HTTPException, Request

from . import config, store

_attempts: dict[str, list[float]] = {}


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    return salt.hex() + ":" + hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1).hex()


def check_password(password: str, stored: str) -> bool:
    salt_hex, _ = stored.split(":")
    return hmac.compare_digest(hash_password(password, bytes.fromhex(salt_hex)), stored)


def rate_limit(key: str, limit: int, per_seconds: int):
    """Small in-process limiter for login, chat and tool routes."""
    now = time.time()
    hits = [t for t in _attempts.get(key, []) if now - t < per_seconds]
    if len(hits) >= limit:
        raise HTTPException(429, "Too many requests. Wait a minute and try again.")
    hits.append(now)
    _attempts[key] = hits


def create_user(merchant_id: str, email: str, password: str, role: str = "owner") -> str:
    if len(password) < 8:
        raise HTTPException(400, "Choose a password of at least 8 characters.")
    uid = str(uuid.uuid4())
    if not store.insert("merchant_users", {"user_id": uid, "merchant_id": merchant_id, "email": email.strip().lower(),
                                           "password_hash": hash_password(password), "role": role, "created_at": store.now()}, or_ignore=True):
        raise HTTPException(409, "An account with that email already exists. Sign in instead.")
    return uid


def open_session(user: dict) -> str:
    token = secrets.token_urlsafe(32)
    expires = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=config.SESSION_HOURS)).isoformat()
    store.insert("sessions", {"token_hash": hashlib.sha256(token.encode()).hexdigest(), "user_id": user["user_id"],
                              "merchant_id": user["merchant_id"], "role": user["role"], "expires_at": expires})
    return token


def login(email: str, password: str, ip: str = "") -> dict:
    rate_limit(f"login:{ip}:{email.lower()}", 8, 60)
    user = store.one("SELECT * FROM merchant_users WHERE email = ?", [email.strip().lower()])
    if not user or not check_password(password, user["password_hash"]):
        store.audit(email, "auth.login", result="denied")
        raise HTTPException(401, "That email and password do not match an account.")
    store.audit(email, "auth.login", merchant_id=user["merchant_id"])
    return {"token": open_session(user), "merchant_id": user["merchant_id"], "role": user["role"]}


def current(authorization: str | None) -> dict | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    s = store.one("SELECT * FROM sessions WHERE token_hash = ?", [hashlib.sha256(authorization[7:].strip().encode()).hexdigest()])
    if not s or s["expires_at"] < store.now():
        return None
    return s


def require_merchant(merchant_id: str, request: Request, authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency: the caller must hold a session for exactly this merchant."""
    s = current(authorization)
    if not s:
        raise HTTPException(401, "Sign in to open this workspace.")
    if s["merchant_id"] != merchant_id:
        store.audit(s["user_id"], "access.denied", target=f"{request.method} {request.url.path}", result="denied",
                    merchant_id=merchant_id, detail={"session_merchant": s["merchant_id"]})
        raise HTTPException(403, "This workspace belongs to another business.")
    return s


def seed_demo_owners():
    """The demo shops get a row in the operational store and a public demo owner, so judges can open their studios.
    They hold sandbox data only. Their orders stay in landing; only workspaces are exported from this store."""
    from . import warehouse
    for d in warehouse.rows("SELECT * FROM gold.dim_merchant WHERE origin = 'demo'"):
        store.insert("merchants", {"merchant_id": d["merchant_id"], "name": d["merchant_name"], "business_type": d["business_type"],
                                   "category": d["category"], "region": d["region"], "sells": d["sells"], "ships_from": d["ships_from"],
                                   "returns_policy": d["returns_policy"], "passport_published": 1, "origin": "demo", "created_at": store.now()}, or_ignore=True)
        store.insert("merchant_connections", {"connection_id": str(uuid.uuid4()), "merchant_id": d["merchant_id"], "provider": "paypal",
                                              "scopes": "orders:read orders:write tracking:write", "status": "active",
                                              "detail": "Demo sandbox app", "created_at": store.now()}, or_ignore=True)
        email = f"{d['merchant_id']}@demo.realdealseal.example"
        store.insert("merchant_users", {"user_id": str(uuid.uuid4()), "merchant_id": d["merchant_id"], "email": email,
                                        "password_hash": hash_password(config.DEMO_PASSWORD), "role": "owner", "created_at": store.now()}, or_ignore=True)
