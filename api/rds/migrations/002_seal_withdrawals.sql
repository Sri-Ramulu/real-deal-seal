-- Real Deal Seal can withdraw one business's seal for cause (fraud reports, PayPal limiting the account, unresolved
-- complaints) without touching anyone else's. Reinstating keeps the history.
CREATE TABLE seal_withdrawals (
    withdrawal_id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL, reason TEXT NOT NULL,
    withdrawn_at TEXT NOT NULL, reinstated_at TEXT, reinstate_note TEXT);
CREATE INDEX seal_withdrawals_by_merchant ON seal_withdrawals (merchant_id, withdrawn_at);
