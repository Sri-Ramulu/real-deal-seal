-- Operational store. Source truth (orders, events), consent and commercial action, one tenant key on every row.
-- Written in portable SQL: runs on SQLite here and is meant to run unchanged on PostgreSQL.
CREATE TABLE merchants (
    merchant_id TEXT PRIMARY KEY, name TEXT NOT NULL, business_type TEXT NOT NULL CHECK (business_type IN ('physical','services','digital','local')),
    category TEXT NOT NULL, region TEXT NOT NULL, sells TEXT, ships_from TEXT, returns_policy TEXT,
    status TEXT NOT NULL DEFAULT 'active', passport_published INTEGER NOT NULL DEFAULT 0, hidden_metrics TEXT NOT NULL DEFAULT '[]',
    origin TEXT NOT NULL DEFAULT 'workspace', created_at TEXT NOT NULL);
CREATE TABLE merchant_users (
    user_id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id), email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK (role IN ('owner','staff')), created_at TEXT NOT NULL);
CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES merchant_users(user_id), merchant_id TEXT NOT NULL, role TEXT NOT NULL, expires_at TEXT NOT NULL);
CREATE TABLE merchant_connections (
    connection_id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id), provider TEXT NOT NULL, scopes TEXT NOT NULL,
    status TEXT NOT NULL, detail TEXT, created_at TEXT NOT NULL, UNIQUE (merchant_id, provider));
CREATE TABLE consent_grants (
    grant_id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id), purpose TEXT NOT NULL, recipient TEXT NOT NULL,
    scope TEXT NOT NULL, consent_version TEXT NOT NULL, share_token_hash TEXT UNIQUE, granted_at TEXT NOT NULL, revoked_at TEXT);
CREATE TABLE catalog_items (
    sku TEXT PRIMARY KEY, merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id), name TEXT NOT NULL, price_usd TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD', stock INTEGER NOT NULL, tags TEXT NOT NULL DEFAULT '[]', description TEXT, updated_at TEXT NOT NULL);
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL, seq INTEGER NOT NULL, order_date TEXT NOT NULL, amount_usd TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD', status TEXT NOT NULL, source_system TEXT NOT NULL, payer_key TEXT, item_count INTEGER NOT NULL DEFAULT 1,
    capture_id TEXT UNIQUE, capture_status TEXT, invoice_id TEXT, simulated INTEGER NOT NULL DEFAULT 0, recorded_at TEXT NOT NULL);
CREATE INDEX orders_by_merchant ON orders (merchant_id, order_date);
CREATE TABLE payment_events (
    event_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, merchant_id TEXT NOT NULL, event_type TEXT NOT NULL CHECK (event_type IN ('capture','refund','dispute_lost','dispute_won')),
    amount_usd TEXT NOT NULL, event_date TEXT NOT NULL, provider_ref TEXT, reason TEXT, evidence_class TEXT NOT NULL, recorded_at TEXT NOT NULL);
CREATE TABLE fulfillment_events (
    event_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, merchant_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN ('shipped','tracking_added','service_completed','digital_delivered','booking_kept','cancelled_by_business')),
    days_after_payment INTEGER, reference TEXT, evidence_class TEXT NOT NULL, recorded_at TEXT NOT NULL);
CREATE TABLE source_evidence (
    evidence_id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL, source TEXT NOT NULL, kind TEXT NOT NULL, sha256 TEXT NOT NULL, rows_accepted INTEGER NOT NULL,
    rows_rejected INTEGER NOT NULL, status TEXT NOT NULL, detail TEXT, retrieved_at TEXT NOT NULL);
CREATE TABLE credentials (
    credential_id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL, kind TEXT NOT NULL CHECK (kind IN ('passport','statement')),
    status TEXT NOT NULL CHECK (status IN ('active','superseded','revoked')), key_id TEXT NOT NULL, data_as_of TEXT, issued_at TEXT NOT NULL,
    valid_until TEXT NOT NULL, status_reason TEXT, document TEXT NOT NULL);
CREATE INDEX credentials_by_merchant ON credentials (merchant_id, kind, status);
CREATE TABLE checkout_sessions (
    session_id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE NOT NULL, sku TEXT NOT NULL, quantity INTEGER NOT NULL, merchant_id TEXT NOT NULL,
    amount_usd TEXT NOT NULL, mode TEXT NOT NULL, status TEXT NOT NULL, paypal_order_id TEXT UNIQUE, capture_id TEXT, approve_url TEXT,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE agent_decisions (
    decision_id TEXT PRIMARY KEY, at TEXT NOT NULL, request TEXT NOT NULL, mode TEXT NOT NULL, model TEXT, evidence_enabled INTEGER NOT NULL,
    pick_sku TEXT, pick_merchant_id TEXT, tools TEXT NOT NULL, answer TEXT NOT NULL);
CREATE TABLE coach_actions (
    action_id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL, rule TEXT NOT NULL, kind TEXT NOT NULL, target_order_id TEXT, status TEXT NOT NULL,
    before_value TEXT, after_value TEXT, detail TEXT, created_at TEXT NOT NULL, verified_at TEXT);
CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, actor TEXT NOT NULL, merchant_id TEXT, action TEXT NOT NULL, target TEXT, result TEXT, detail TEXT);
CREATE TABLE webhook_events (
    event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, resource_id TEXT, verified INTEGER NOT NULL, outcome TEXT, received_at TEXT NOT NULL);
CREATE TABLE jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
