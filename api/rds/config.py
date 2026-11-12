"""Settings come from the environment. Nothing secret lives in the repo."""
from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    """Read KEY=value lines from .env into the environment. Values already set win, so a host's settings
    (Render, a shell export) always beat the file. Set RDS_NO_DOTENV=1 to skip it, as the tests do."""
    if os.environ.get("RDS_NO_DOTENV") or not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        if value:
            os.environ.setdefault(key.strip(), value)


_load_dotenv(REPO / ".env")
VAR = Path(os.environ.get("RDS_VAR_DIR", REPO / "var"))
VAR.mkdir(parents=True, exist_ok=True)
# The warehouse the API serves is rebuilt at runtime from landing plus the operational extract, so it lives in var/.
os.environ.setdefault("RDS_EXTRACT_DIR", str(VAR / "extract"))
os.environ.setdefault("RDS_WAREHOUSE", str(VAR / "warehouse" / "rds.duckdb"))
os.environ.setdefault("RDS_CATALOG", str(VAR / "warehouse" / "catalog.json"))

# On Render, RENDER_EXTERNAL_URL is set automatically, so PayPal sends buyers back to the live site, not localhost.
PUBLIC_URL = (os.environ.get("RDS_PUBLIC_URL") or os.environ.get("RENDER_EXTERNAL_URL") or "http://localhost:8000").rstrip("/")
PAYPAL_BASE = os.environ.get("PAYPAL_BASE", "https://api-m.sandbox.paypal.com")
MODEL = os.environ.get("RDS_MODEL", "claude-sonnet-5-5")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
GEMINI_BASE = os.environ.get("GEMINI_BASE", "https://generativelanguage.googleapis.com/v1beta")
# Google's alias for its newest Flash model; pin a specific model id here for a fixed evaluation.
GEMINI_MODEL = os.environ.get("RDS_GEMINI_MODEL", "gemini-flash-latest")
OPUS_MODEL = os.environ.get("RDS_OPUS_MODEL", "claude-opus-5-5")
DEFAULT_ASSISTANT = os.environ.get("RDS_ASSISTANT", "gemini")
DEMO_SHOPS = os.environ.get("RDS_DEMO_SHOPS", "1") == "1"  # the four fictional shops in demo_shops.py join at startup
REFRESH_HOURS = float(os.environ.get("RDS_REFRESH_HOURS", "24"))  # 0 turns the scheduled refresh off

MODEL_CHOICES = {
    "gemini": {"provider": "gemini", "model": GEMINI_MODEL, "label": "Google Gemini"},
    "claude-opus": {"provider": "claude", "model": OPUS_MODEL, "label": "Claude Opus"},
    "claude-sonnet": {"provider": "claude", "model": MODEL, "label": "Claude Sonnet"},
}


def _has_key(provider: str) -> bool:
    return bool(GEMINI_API_KEY if provider == "gemini" else ANTHROPIC_API_KEY)


def model_choices() -> list[dict]:
    return [{"key": k, **v, "available": _has_key(v["provider"]), "default": k == DEFAULT_ASSISTANT} for k, v in MODEL_CHOICES.items()]


def resolve_model(choice: str | None) -> dict | None:
    """Turn a choice key or raw model id into {provider, model, label}. Falls back to the default, then to any model
    with a key. None means no model is set up (offline mode)."""
    if choice and choice not in MODEL_CHOICES:
        provider = "gemini" if choice.startswith("gemini") else "claude" if choice.startswith("claude") else None
        if provider and _has_key(provider):
            label = next((v["label"] for v in MODEL_CHOICES.values() if v["model"] == choice), choice)
            return {"provider": provider, "model": choice, "label": label, "key": choice}
        choice = None
    order = [choice] if choice else []
    order += [DEFAULT_ASSISTANT] + [k for k in MODEL_CHOICES if k != DEFAULT_ASSISTANT]
    for k in order:
        v = MODEL_CHOICES.get(k)
        if v and _has_key(v["provider"]):
            return {**v, "key": k}
    return None
ISSUER_NAME = "Real Deal Seal (hackathon demo issuer; not PayPal)"
SEAL_VALID_DAYS = 45


def paypal_credentials(merchant_id: str) -> tuple[str, str] | None:
    """Each shop has its own PayPal sandbox app: PAYPAL_<SHOP>_CLIENT_ID / _CLIENT_SECRET."""
    p = f"PAYPAL_{merchant_id.upper()}"
    cid, sec = os.environ.get(f"{p}_CLIENT_ID"), os.environ.get(f"{p}_CLIENT_SECRET")
    return (cid, sec) if cid and sec else None


def did() -> str:
    host = PUBLIC_URL.split("://", 1)[1].replace(":", "%3A")
    return f"did:web:{host}"


DEMO_PASSWORD = os.environ.get("RDS_DEMO_PASSWORD", "demo-owner")
PAYPAL_WEBHOOK_ID = os.environ.get("PAYPAL_WEBHOOK_ID", "")


def paypal_webhook_id(merchant_id: str) -> str:
    """Each shop's PayPal app has its own webhook: PAYPAL_<SHOP>_WEBHOOK_ID, falling back to PAYPAL_WEBHOOK_ID."""
    return os.environ.get(f"PAYPAL_{merchant_id.upper()}_WEBHOOK_ID") or PAYPAL_WEBHOOK_ID
SESSION_HOURS = 12
CONSENT_VERSION = "rds-consent-1"
