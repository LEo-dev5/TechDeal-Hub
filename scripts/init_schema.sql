-- TechDeal-Hub 초기 스키마
-- 실행: python -m scripts.init_db

-- 소스 테이블
CREATE TABLE IF NOT EXISTS sources (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(50) NOT NULL UNIQUE,
    base_url   VARCHAR(255) NOT NULL,
    is_active  BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 카테고리 테이블
CREATE TABLE IF NOT EXISTS categories (
    id         SERIAL PRIMARY KEY,
    parent_id  INTEGER REFERENCES categories(id),
    name       VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 딜 테이블
CREATE TABLE IF NOT EXISTS deals (
    id              BIGSERIAL PRIMARY KEY,
    source_id       INTEGER NOT NULL REFERENCES sources(id),
    category_id     INTEGER REFERENCES categories(id),
    source_post_id  VARCHAR(100) NOT NULL,
    title           VARCHAR(500) NOT NULL,
    extracted_model VARCHAR(100),
    price           INTEGER,
    original_price  INTEGER,
    shipping_fee    INTEGER DEFAULT 0,
    currency        VARCHAR(10) DEFAULT 'KRW',
    mall_url        TEXT,
    source_url      TEXT NOT NULL,
    thumbnail_url   TEXT,
    upvotes         INTEGER DEFAULT 0,
    comments_count  INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    posted_at       TIMESTAMPTZ NOT NULL,
    scraped_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source_id, source_post_id)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_deals_active_posted ON deals (is_active, posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_deals_model         ON deals (extracted_model);
CREATE INDEX IF NOT EXISTS idx_deals_category      ON deals (category_id, posted_at DESC);

-- 초기 소스 데이터 (펨코 제외 — robots.txt Disallow:/ 위반)
INSERT INTO sources (name, base_url) VALUES
    ('뽐뿌',     'https://www.ppomppu.co.kr'),
    ('클리앙',   'https://www.clien.net'),
    ('퀘이사존', 'https://quasarzone.com'),
    ('루리웹',   'https://bbs.ruliweb.com')
ON CONFLICT (name) DO NOTHING;

-- 초기 카테고리
INSERT INTO categories (name) VALUES
    ('노트북'),
    ('스마트폰'),
    ('태블릿'),
    ('모니터'),
    ('키보드/마우스'),
    ('스토리지'),
    ('가전'),
    ('기타')
ON CONFLICT DO NOTHING;
