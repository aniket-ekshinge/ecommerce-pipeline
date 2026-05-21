-- ============================================
-- E-Commerce Data Warehouse — Star Schema DDL
-- ============================================

-- Drop in reverse dependency order (safe re-runs)
DROP TABLE IF EXISTS fact_orders CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;
DROP TABLE IF EXISTS dim_geography CASCADE;

-- ──────────────────────────────
-- Dimension: Geography
-- ──────────────────────────────
CREATE TABLE dim_geography (
    country        VARCHAR(100) PRIMARY KEY,
    region         VARCHAR(100),
    continent      VARCHAR(50),
    created_at     TIMESTAMP DEFAULT NOW()
);

-- ──────────────────────────────
-- Dimension: Customer
-- ──────────────────────────────
CREATE TABLE dim_customer (
    customer_id       INTEGER      PRIMARY KEY,
    country           VARCHAR(100),
    is_guest          BOOLEAN      DEFAULT FALSE,
    first_order_date  DATE,
    last_order_date   DATE,
    total_orders      INTEGER      DEFAULT 0,
    created_at        TIMESTAMP    DEFAULT NOW(),
    updated_at        TIMESTAMP    DEFAULT NOW()
);

-- ──────────────────────────────
-- Dimension: Product
-- ──────────────────────────────
CREATE TABLE dim_product (
    stock_code     VARCHAR(20)  PRIMARY KEY,
    description    TEXT,
    avg_price      NUMERIC(10,2),
    times_ordered  INTEGER      DEFAULT 0,
    created_at     TIMESTAMP    DEFAULT NOW(),
    updated_at     TIMESTAMP    DEFAULT NOW()
);

-- ──────────────────────────────
-- Dimension: Date  (pre-populated in step 4)
-- ──────────────────────────────
CREATE TABLE dim_date (
    date_id        INTEGER      PRIMARY KEY,   -- YYYYMMDD integer key
    full_date      DATE         NOT NULL UNIQUE,
    year           SMALLINT     NOT NULL,
    quarter        SMALLINT     NOT NULL,
    month          SMALLINT     NOT NULL,
    month_name     VARCHAR(10)  NOT NULL,
    day            SMALLINT     NOT NULL,
    day_of_week    VARCHAR(10)  NOT NULL,
    week_of_year   SMALLINT     NOT NULL,
    is_weekend     BOOLEAN      NOT NULL DEFAULT FALSE
);

-- ──────────────────────────────
-- Fact: Orders  (centre of the star)
-- ──────────────────────────────
CREATE TABLE fact_orders (
    order_line_id  BIGSERIAL    PRIMARY KEY,
    invoice_id     VARCHAR(20)  NOT NULL,
    stock_code     VARCHAR(20)  NOT NULL REFERENCES dim_product(stock_code),
    customer_id    INTEGER      NOT NULL REFERENCES dim_customer(customer_id),
    date_id        INTEGER      NOT NULL REFERENCES dim_date(date_id),
    country        VARCHAR(100) NOT NULL REFERENCES dim_geography(country),
    quantity       INTEGER      NOT NULL,
    unit_price     NUMERIC(10,2) NOT NULL,
    revenue        NUMERIC(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    is_cancelled   BOOLEAN      NOT NULL DEFAULT FALSE,
    loaded_at      TIMESTAMP    DEFAULT NOW()
);

-- ──────────────────────────────
-- Indexes for query performance
-- ──────────────────────────────
CREATE INDEX idx_orders_customer  ON fact_orders(customer_id);
CREATE INDEX idx_orders_product   ON fact_orders(stock_code);
CREATE INDEX idx_orders_date      ON fact_orders(date_id);
CREATE INDEX idx_orders_country   ON fact_orders(country);
CREATE INDEX idx_orders_invoice   ON fact_orders(invoice_id);
CREATE INDEX idx_date_full        ON dim_date(full_date);
CREATE INDEX idx_date_yearmonth   ON dim_date(year, month);

-- ──────────────────────────────
-- Metadata table for ETL audit trail
-- ──────────────────────────────
CREATE TABLE etl_log (
    log_id         SERIAL       PRIMARY KEY,
    run_timestamp  TIMESTAMP    DEFAULT NOW(),
    rows_extracted INTEGER,
    rows_loaded    INTEGER,
    rows_skipped   INTEGER,
    status         VARCHAR(20),
    notes          TEXT
);

SELECT 'Schema created successfully' AS status;