-- Egypt Phone Prices — PostgreSQL schema
-- Run this manually or let Alembic manage it via migrations.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── Brands ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS brands (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(100) NOT NULL UNIQUE,
    slug       VARCHAR(100) NOT NULL UNIQUE,
    logo_url   VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Devices ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS devices (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id       UUID         NOT NULL REFERENCES brands(id),
    name           VARCHAR(200) NOT NULL,
    slug           VARCHAR(200) NOT NULL UNIQUE,
    gsmarena_url   VARCHAR(500),
    image_url      VARCHAR(500),
    display        VARCHAR(200),
    chipset        VARCHAR(200),
    ram            VARCHAR(100),
    storage        VARCHAR(100),
    camera         VARCHAR(200),
    battery        VARCHAR(100),
    os             VARCHAR(100),
    release_year   INT,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_devices_brand ON devices(brand_id);
CREATE INDEX IF NOT EXISTS idx_devices_release ON devices(release_year DESC);

-- ─── Retailers ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS retailers (
    id        UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name      VARCHAR(100) NOT NULL UNIQUE,
    slug      VARCHAR(100) NOT NULL UNIQUE,
    base_url  VARCHAR(300) NOT NULL,
    logo_url  VARCHAR(500),
    is_active BOOLEAN      NOT NULL DEFAULT TRUE
);

-- Seed retailers
INSERT INTO retailers (name, slug, base_url) VALUES
    ('Jumia Egypt',   'jumia',     'https://www.jumia.com.eg'),
    ('Noon Egypt',    'noon',      'https://www.noon.com/egypt-en/'),
    ('B.Tech',        'btech',     'https://btech.com'),
    ('Amazon Egypt',  'amazon_eg', 'https://www.amazon.eg')
ON CONFLICT DO NOTHING;

-- ─── Prices ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prices (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id            UUID        NOT NULL REFERENCES devices(id),
    retailer_id          UUID        NOT NULL REFERENCES retailers(id),
    price_egp            NUMERIC(10,2) NOT NULL,
    original_price_egp   NUMERIC(10,2),
    product_url          VARCHAR(1000) NOT NULL,
    in_stock             BOOLEAN     NOT NULL DEFAULT TRUE,
    scraped_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prices_device    ON prices(device_id);
CREATE INDEX IF NOT EXISTS idx_prices_scraped   ON prices(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_prices_device_ts ON prices(device_id, scraped_at DESC);

-- ─── Scrape Logs ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scrape_logs (
    id               BIGSERIAL PRIMARY KEY,
    retailer_slug    VARCHAR(100) NOT NULL,
    status           VARCHAR(20)  NOT NULL,
    devices_scraped  INT          NOT NULL DEFAULT 0,
    error_message    TEXT,
    started_at       TIMESTAMPTZ  NOT NULL,
    finished_at      TIMESTAMPTZ
);

-- ─── Price history view ──────────────────────────────────
CREATE OR REPLACE VIEW price_history AS
SELECT
    d.id        AS device_id,
    d.name      AS device_name,
    b.name      AS brand,
    r.name      AS retailer,
    p.price_egp,
    p.in_stock,
    DATE(p.scraped_at) AS price_date,
    MIN(p.price_egp) OVER (
        PARTITION BY p.device_id, r.id, DATE(p.scraped_at)
    ) AS daily_low
FROM prices p
JOIN devices  d ON d.id = p.device_id
JOIN brands   b ON b.id = d.brand_id
JOIN retailers r ON r.id = p.retailer_id;
