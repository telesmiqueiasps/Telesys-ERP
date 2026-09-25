export const COMPANY_SCHEMA_SQL = `
-- Table: sync_queue (Fila de eventos de sincronização offline-first)
CREATE TABLE IF NOT EXISTS sync_queue (
    id TEXT PRIMARY KEY,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    operation TEXT NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    payload TEXT NOT NULL,   -- JSON string do evento
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'SYNCED', 'FAILED'
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    last_attempt_at TEXT
);

-- Table: local_products (Catálogo local de produtos para o PDV)
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

-- Table: local_cash_registers (Caixa local)
CREATE TABLE IF NOT EXISTS local_cash_registers (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'CLOSED'
    opened_at TEXT NOT NULL DEFAULT (datetime('now')),
    closed_at TEXT,
    initial_amount REAL NOT NULL DEFAULT 0.0,
    current_amount REAL NOT NULL DEFAULT 0.0
);

-- Table: local_sales (Vendas locais registradas no PDV)
CREATE TABLE IF NOT EXISTS local_sales (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    customer_id TEXT,
    total_amount REAL NOT NULL DEFAULT 0.0,
    discount_amount REAL NOT NULL DEFAULT 0.0,
    net_amount REAL NOT NULL DEFAULT 0.0,
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'COMPLETED', -- 'COMPLETED', 'CANCELED'
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    synced INTEGER NOT NULL DEFAULT 0
);

-- Table: local_sale_items (Itens da venda local)
CREATE TABLE IF NOT EXISTS local_sale_items (
    id TEXT PRIMARY KEY,
    sale_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity REAL NOT NULL,
    total_price REAL NOT NULL,
    FOREIGN KEY(sale_id) REFERENCES local_sales(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON local_products(barcode);
CREATE INDEX IF NOT EXISTS idx_sales_created ON local_sales(created_at);
`;
