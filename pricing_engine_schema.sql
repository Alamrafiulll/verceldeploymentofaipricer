-- Chin Hin AI Pricing Strategist
-- Standalone prototype schema for Azure Database for PostgreSQL
-- Safe to re-run (idempotent where possible)

BEGIN;

CREATE SCHEMA IF NOT EXISTS pricing_engine;

-- =========================
-- 1) Users
-- =========================
CREATE TABLE IF NOT EXISTS pricing_engine.users (
    user_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('sales_manager', 'senior_management', 'admin')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 2) Customers
-- =========================
CREATE TABLE IF NOT EXISTS pricing_engine.customers (
    customer_id BIGSERIAL PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL UNIQUE,
    tier VARCHAR(50) NOT NULL CHECK (tier IN ('Strategic', 'Core', 'Growth')),
    region VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 3) Products
-- =========================
CREATE TABLE IF NOT EXISTS pricing_engine.products (
    product_id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    cost_price NUMERIC(12,2) NOT NULL CHECK (cost_price >= 0),
    base_price NUMERIC(12,2) NOT NULL CHECK (base_price >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 4) Inventory
-- =========================
CREATE TABLE IF NOT EXISTS pricing_engine.inventory (
    inventory_id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES pricing_engine.products(product_id) ON DELETE CASCADE,
    quantity_available INT NOT NULL CHECK (quantity_available >= 0),
    stock_entry_date DATE NOT NULL DEFAULT CURRENT_DATE,
    warehouse_location VARCHAR(100) NOT NULL
);

-- =========================
-- 5) Historical Sales (AI training base)
-- =========================
CREATE TABLE IF NOT EXISTS pricing_engine.sales_history (
    sale_id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES pricing_engine.products(product_id) ON DELETE RESTRICT,
    customer_id BIGINT NOT NULL REFERENCES pricing_engine.customers(customer_id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    selling_price NUMERIC(12,2) NOT NULL CHECK (selling_price >= 0),
    discount_percent NUMERIC(5,2) NOT NULL CHECK (discount_percent >= 0 AND discount_percent <= 100),
    margin_percent NUMERIC(6,2) NOT NULL,
    channel VARCHAR(50) NOT NULL CHECK (channel IN ('traditional', 'corporate', 'ecommerce', 'project')),
    sale_date DATE NOT NULL
);

-- =========================
-- 6) Deal Requests
-- =========================
CREATE TABLE IF NOT EXISTS pricing_engine.deal_requests (
    deal_id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES pricing_engine.products(product_id) ON DELETE RESTRICT,
    customer_id BIGINT NOT NULL REFERENCES pricing_engine.customers(customer_id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    requested_discount NUMERIC(5,2) CHECK (requested_discount >= 0 AND requested_discount <= 100),
    competitor_price NUMERIC(12,2) CHECK (competitor_price >= 0),
    created_by BIGINT NOT NULL REFERENCES pricing_engine.users(user_id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 7) AI Recommendations
-- =========================
CREATE TABLE IF NOT EXISTS pricing_engine.ai_recommendations (
    recommendation_id BIGSERIAL PRIMARY KEY,
    deal_id BIGINT NOT NULL REFERENCES pricing_engine.deal_requests(deal_id) ON DELETE CASCADE,
    recommended_price NUMERIC(12,2) NOT NULL CHECK (recommended_price >= 0),
    recommended_discount NUMERIC(5,2) NOT NULL CHECK (recommended_discount >= 0 AND recommended_discount <= 100),
    predicted_margin NUMERIC(6,2) NOT NULL,
    win_probability NUMERIC(5,2) NOT NULL CHECK (win_probability >= 0 AND win_probability <= 100),
    confidence_score NUMERIC(5,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 100),
    explanation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 8) Approved Deals
-- =========================
CREATE TABLE IF NOT EXISTS pricing_engine.approved_deals (
    approval_id BIGSERIAL PRIMARY KEY,
    deal_id BIGINT NOT NULL UNIQUE REFERENCES pricing_engine.deal_requests(deal_id) ON DELETE CASCADE,
    final_price NUMERIC(12,2) NOT NULL CHECK (final_price >= 0),
    final_discount NUMERIC(5,2) NOT NULL CHECK (final_discount >= 0 AND final_discount <= 100),
    approved_by BIGINT NOT NULL REFERENCES pricing_engine.users(user_id) ON DELETE RESTRICT,
    approval_reason TEXT,
    approved_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 9) Audit Logs
-- =========================
CREATE TABLE IF NOT EXISTS pricing_engine.audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES pricing_engine.users(user_id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    entity_id BIGINT,
    action_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 10) Performance Indexes
-- =========================
CREATE INDEX IF NOT EXISTS idx_sales_product
    ON pricing_engine.sales_history(product_id);

CREATE INDEX IF NOT EXISTS idx_sales_customer
    ON pricing_engine.sales_history(customer_id);

CREATE INDEX IF NOT EXISTS idx_sales_sale_date
    ON pricing_engine.sales_history(sale_date);

CREATE INDEX IF NOT EXISTS idx_deal_product
    ON pricing_engine.deal_requests(product_id);

CREATE INDEX IF NOT EXISTS idx_deal_customer
    ON pricing_engine.deal_requests(customer_id);

CREATE INDEX IF NOT EXISTS idx_ai_reco_deal
    ON pricing_engine.ai_recommendations(deal_id);

CREATE INDEX IF NOT EXISTS idx_audit_entity
    ON pricing_engine.audit_logs(entity, entity_id);

-- =========================
-- 11) Seed Data
-- =========================
INSERT INTO pricing_engine.users (name, email, password_hash, role, is_active)
VALUES
    ('Admin User', 'admin@chinhin.local', '$2b$12$exampleReplaceWithBcryptHash', 'admin', TRUE),
    ('Sales Manager', 'sales@chinhin.local', '$2b$12$exampleReplaceWithBcryptHash', 'sales_manager', TRUE),
    ('Senior Management', 'director@chinhin.local', '$2b$12$exampleReplaceWithBcryptHash', 'senior_management', TRUE)
ON CONFLICT (email) DO NOTHING;

INSERT INTO pricing_engine.customers (customer_name, tier, region)
VALUES
    ('ABC Hardware', 'Strategic', 'KL'),
    ('Mega Builders', 'Core', 'Selangor'),
    ('Prime Construction', 'Growth', 'Penang')
ON CONFLICT (customer_name) DO UPDATE
SET tier = EXCLUDED.tier,
    region = EXCLUDED.region;

INSERT INTO pricing_engine.products (sku, product_name, category, cost_price, base_price)
VALUES
    ('CEM001', 'Portland Cement', 'Construction', 18.00, 25.00),
    ('STEEL01', 'Steel Mesh', 'Construction', 45.00, 70.00)
ON CONFLICT (sku) DO UPDATE
SET product_name = EXCLUDED.product_name,
    category = EXCLUDED.category,
    cost_price = EXCLUDED.cost_price,
    base_price = EXCLUDED.base_price;

INSERT INTO pricing_engine.inventory (product_id, quantity_available, stock_entry_date, warehouse_location)
SELECT p.product_id, 300, CURRENT_DATE - INTERVAL '90 days', 'Warehouse-KL'
FROM pricing_engine.products p
WHERE p.sku = 'CEM001'
  AND NOT EXISTS (
      SELECT 1
      FROM pricing_engine.inventory i
      WHERE i.product_id = p.product_id
        AND i.warehouse_location = 'Warehouse-KL'
  );

INSERT INTO pricing_engine.inventory (product_id, quantity_available, stock_entry_date, warehouse_location)
SELECT p.product_id, 120, CURRENT_DATE - INTERVAL '30 days', 'Warehouse-Selangor'
FROM pricing_engine.products p
WHERE p.sku = 'STEEL01'
  AND NOT EXISTS (
      SELECT 1
      FROM pricing_engine.inventory i
      WHERE i.product_id = p.product_id
        AND i.warehouse_location = 'Warehouse-Selangor'
  );

INSERT INTO pricing_engine.sales_history
    (product_id, customer_id, quantity, selling_price, discount_percent, margin_percent, channel, sale_date)
SELECT p.product_id, c.customer_id, 120, 24.00, 4.00, 25.00, 'traditional', CURRENT_DATE - INTERVAL '10 days'
FROM pricing_engine.products p
JOIN pricing_engine.customers c ON c.customer_name = 'ABC Hardware'
WHERE p.sku = 'CEM001'
  AND NOT EXISTS (
      SELECT 1
      FROM pricing_engine.sales_history s
      WHERE s.product_id = p.product_id
        AND s.customer_id = c.customer_id
        AND s.sale_date = CURRENT_DATE - INTERVAL '10 days'
  );

INSERT INTO pricing_engine.sales_history
    (product_id, customer_id, quantity, selling_price, discount_percent, margin_percent, channel, sale_date)
SELECT p.product_id, c.customer_id, 60, 66.00, 5.70, 31.80, 'project', CURRENT_DATE - INTERVAL '3 days'
FROM pricing_engine.products p
JOIN pricing_engine.customers c ON c.customer_name = 'Mega Builders'
WHERE p.sku = 'STEEL01'
  AND NOT EXISTS (
      SELECT 1
      FROM pricing_engine.sales_history s
      WHERE s.product_id = p.product_id
        AND s.customer_id = c.customer_id
        AND s.sale_date = CURRENT_DATE - INTERVAL '3 days'
  );

-- Seed one deal request and one AI recommendation
INSERT INTO pricing_engine.deal_requests
    (product_id, customer_id, quantity, requested_discount, competitor_price, created_by)
SELECT p.product_id, c.customer_id, 80, 6.00, 23.50, u.user_id
FROM pricing_engine.products p
JOIN pricing_engine.customers c ON c.customer_name = 'ABC Hardware'
JOIN pricing_engine.users u ON u.email = 'sales@chinhin.local'
WHERE p.sku = 'CEM001'
  AND NOT EXISTS (
      SELECT 1
      FROM pricing_engine.deal_requests d
      WHERE d.product_id = p.product_id
        AND d.customer_id = c.customer_id
        AND d.created_by = u.user_id
  );

INSERT INTO pricing_engine.ai_recommendations
    (deal_id, recommended_price, recommended_discount, predicted_margin, win_probability, confidence_score, explanation)
SELECT d.deal_id, 24.20, 3.20, 25.60, 82.00, 88.00,
       'Recommended due to strategic customer tier and aging stock profile.'
FROM pricing_engine.deal_requests d
WHERE NOT EXISTS (
    SELECT 1
    FROM pricing_engine.ai_recommendations r
    WHERE r.deal_id = d.deal_id
);

COMMIT;

-- =========================
-- 12) Validation Query
-- =========================
-- Run this after script execution:
-- SELECT
--     p.product_name,
--     AVG(s.selling_price) AS avg_price,
--     AVG(s.discount_percent) AS avg_discount,
--     AVG(s.margin_percent) AS avg_margin
-- FROM pricing_engine.sales_history s
-- JOIN pricing_engine.products p
--     ON s.product_id = p.product_id
-- GROUP BY p.product_name
-- ORDER BY p.product_name;

