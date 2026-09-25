-- Telesys ERP Database Initialization
-- Extensions foundation for UUID and cryptographic functions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Log completion of initialization
DO $$
BEGIN
    RAISE NOTICE 'Telesys ERP database extensions initialized successfully.';
END $$;
