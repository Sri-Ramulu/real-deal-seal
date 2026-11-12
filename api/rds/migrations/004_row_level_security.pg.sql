-- PostgreSQL only. Row-level security: inside a request scoped to one business (app.merchant_id set by the API),
-- the database returns and accepts only that business's rows. An empty scope is system work (refresh, webhooks).
-- FORCE applies the policies to the table owner too, which is the role the app connects as.
ALTER TABLE merchants ENABLE ROW LEVEL SECURITY;
ALTER TABLE merchants FORCE ROW LEVEL SECURITY;
CREATE POLICY merchants_tenant ON merchants USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE merchant_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE merchant_users FORCE ROW LEVEL SECURITY;
CREATE POLICY merchant_users_tenant ON merchant_users USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE merchant_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE merchant_connections FORCE ROW LEVEL SECURITY;
CREATE POLICY merchant_connections_tenant ON merchant_connections USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE consent_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_grants FORCE ROW LEVEL SECURITY;
CREATE POLICY consent_grants_tenant ON consent_grants USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE catalog_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE catalog_items FORCE ROW LEVEL SECURITY;
CREATE POLICY catalog_items_tenant ON catalog_items USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
CREATE POLICY orders_tenant ON orders USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events FORCE ROW LEVEL SECURITY;
CREATE POLICY payment_events_tenant ON payment_events USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE fulfillment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE fulfillment_events FORCE ROW LEVEL SECURITY;
CREATE POLICY fulfillment_events_tenant ON fulfillment_events USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE source_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_evidence FORCE ROW LEVEL SECURITY;
CREATE POLICY source_evidence_tenant ON source_evidence USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE credentials FORCE ROW LEVEL SECURITY;
CREATE POLICY credentials_tenant ON credentials USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE checkout_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkout_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY checkout_sessions_tenant ON checkout_sessions USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE coach_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE coach_actions FORCE ROW LEVEL SECURITY;
CREATE POLICY coach_actions_tenant ON coach_actions USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
ALTER TABLE seal_withdrawals ENABLE ROW LEVEL SECURITY;
ALTER TABLE seal_withdrawals FORCE ROW LEVEL SECURITY;
CREATE POLICY seal_withdrawals_tenant ON seal_withdrawals USING (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true))
    WITH CHECK (coalesce(current_setting('app.merchant_id', true), '') = '' OR merchant_id = current_setting('app.merchant_id', true));
