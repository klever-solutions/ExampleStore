-- ============================================================
-- kleverRetail Cloud SQL Schema
-- Version: 1.0
-- ============================================================

-- ---------- STORES ----------
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    code VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    city VARCHAR(64),
    active BOOLEAN DEFAULT TRUE
);

-- ---------- STAFF ----------
CREATE TABLE staff (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    role VARCHAR(32) DEFAULT 'staff',
    active BOOLEAN DEFAULT TRUE
);

-- ---------- ITEMS ----------
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    code VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    stock INTEGER DEFAULT 0,
    UNIQUE(store_id, code)
);

-- ---------- ORDERS ----------
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(10,2) NOT NULL,
    staff_username VARCHAR(64),
    discount NUMERIC(10,2) DEFAULT 0
);

-- ---------- ORDER LINES ----------
CREATE TABLE order_lines (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    item_name VARCHAR(128) NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    qty INTEGER NOT NULL
);

-- ============================================================
-- DEFAULT DATA
-- ============================================================

INSERT INTO stores (code, name, city) VALUES
('HRG-001', 'Harrogate Superstore', 'Harrogate');

INSERT INTO staff (username, name, role) VALUES
('admin', 'Admin', 'manager');

INSERT INTO items (store_id, code, name, price, stock) VALUES
(1, '1001', 'Milk', 1.20, 50),
(1, '1002', 'Bread', 0.80, 40),
(1, '1003', 'Eggs', 2.00, 30);
