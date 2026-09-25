export const MASTER_SCHEMA_SQL = `
-- Table: app_settings (Configurações da instalação local)
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Table: local_companies (Empresas autorizadas no aplicativo desktop)
CREATE TABLE IF NOT EXISTS local_companies (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    trade_name TEXT,
    cnpj TEXT,
    state_registration TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Table: local_session (Cache de sessão e estado de login)
CREATE TABLE IF NOT EXISTS local_session (
    id TEXT PRIMARY KEY DEFAULT 'current_session',
    token TEXT,
    refresh_token TEXT,
    user_id TEXT,
    user_email TEXT,
    user_name TEXT,
    active_company_id TEXT,
    last_sync_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_local_companies_tenant ON local_companies(tenant_id);
`;
