import os
import sqlite3

BASE_DIR = r"C:\ProgramData\telesys"
DATA_DIR = os.path.join(BASE_DIR, "data")
EMPRESAS_DIR = os.path.join(DATA_DIR, "empresas")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
BACKUPS_DIR = os.path.join(DATA_DIR, "backups")

# 1. Create directories
for directory in [BASE_DIR, DATA_DIR, EMPRESAS_DIR, LOGS_DIR, CACHE_DIR, CONFIG_DIR, BACKUPS_DIR]:
    os.makedirs(directory, exist_ok=True)
    print(f"Diretorio garantido: {directory}")

# 2. Create master.db
master_db_path = os.path.join(DATA_DIR, "master.db")
conn_master = sqlite3.connect(master_db_path)
cur_master = conn_master.cursor()

cur_master.executescript("""
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

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
""")

# Insert initial settings record
cur_master.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('installation_version', '0.1.0')")
cur_master.execute("INSERT OR REPLACE INTO app_settings (key, value) VALUES ('local_path', ?)", (DATA_DIR,))
conn_master.commit()
conn_master.close()
print(f"Banco SQLite master.db criado em: {master_db_path}")

# 3. Create sample company database
company_id = "98df5bdd-ab57-4d5e-82d3-b4c1c7eba103"
company_db_path = os.path.join(EMPRESAS_DIR, f"empresa_{company_id}.db")
conn_company = sqlite3.connect(company_db_path)
cur_company = conn_company.cursor()

cur_company.executescript("""
CREATE TABLE IF NOT EXISTS sync_queue (
    id TEXT PRIMARY KEY,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'PENDING',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    last_attempt_at TEXT
);

CREATE TABLE IF NOT EXISTS local_products (
    id TEXT PRIMARY KEY,
    code TEXT,
    name TEXT NOT NULL,
    barcode TEXT,
    unit TEXT DEFAULT 'UN',
    price REAL NOT NULL DEFAULT 0.0,
    cost REAL NOT NULL DEFAULT 0.0,
    stock_qty REAL NOT NULL DEFAULT 0.0,
    min_stock_qty REAL NOT NULL DEFAULT 0.0,
    is_active INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS local_cash_registers (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    opened_at TEXT NOT NULL DEFAULT (datetime('now')),
    closed_at TEXT,
    initial_amount REAL NOT NULL DEFAULT 0.0,
    current_amount REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS local_sales (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    customer_id TEXT,
    total_amount REAL NOT NULL DEFAULT 0.0,
    discount_amount REAL NOT NULL DEFAULT 0.0,
    net_amount REAL NOT NULL DEFAULT 0.0,
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'COMPLETED',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    synced INTEGER NOT NULL DEFAULT 0
);
""")

conn_company.commit()
conn_company.close()
print(f"Banco SQLite da empresa criado em: {company_db_path}")

print("Estrutura de diretorios e arquivos SQLite gerados no disco C: com sucesso!")
