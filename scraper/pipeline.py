"""
크롤링 파이프라인: 수집 → 모델명 추출 → DB Upsert
"""
import os
from datetime import datetime
from typing import Optional

import psycopg2
import psycopg2.extras

from scraper.extractor import extract_category_hint, extract_model
from scraper.sites import ppomppu, clien, fmkorea, quasarzone, ruliweb

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://techdeal:changeme@localhost:5432/techdeal")

# 소스 이름 → DB source_id 캐시
_source_id_cache: dict[str, int] = {}
_category_id_cache: dict[str, int] = {}


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def get_source_id(conn, name: str) -> Optional[int]:
    if name in _source_id_cache:
        return _source_id_cache[name]
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM sources WHERE name = %s", (name,))
        row = cur.fetchone()
        if row:
            _source_id_cache[name] = row[0]
            return row[0]
    return None


def get_category_id(conn, name: str) -> Optional[int]:
    if name in _category_id_cache:
        return _category_id_cache[name]
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM categories WHERE name = %s", (name,))
        row = cur.fetchone()
        if row:
            _category_id_cache[name] = row[0]
            return row[0]
    return None


UPSERT_SQL = """
INSERT INTO deals (
    source_id, category_id, source_post_id, title,
    extracted_model, price, shipping_fee, currency,
    mall_url, source_url, thumbnail_url,
    upvotes, comments_count, is_active, posted_at
) VALUES (
    %(source_id)s, %(category_id)s, %(source_post_id)s, %(title)s,
    %(extracted_model)s, %(price)s, %(shipping_fee)s, %(currency)s,
    %(mall_url)s, %(source_url)s, %(thumbnail_url)s,
    %(upvotes)s, %(comments_count)s, %(is_active)s, %(posted_at)s
)
ON CONFLICT (source_id, source_post_id)
DO UPDATE SET
    upvotes        = EXCLUDED.upvotes,
    comments_count = EXCLUDED.comments_count,
    is_active      = EXCLUDED.is_active,
    updated_at     = CURRENT_TIMESTAMP
RETURNING id, (xmax = 0) AS inserted
"""


def upsert_deal(conn, source_name: str, raw) -> tuple[int, bool]:
    """
    단일 딜 Upsert

    Returns:
        (deal_id, is_new): deal_id와 신규 여부
    """
    source_id = get_source_id(conn, source_name)
    if source_id is None:
        raise ValueError(f"소스를 찾을 수 없음: {source_name}")

    category_hint = extract_category_hint(raw.title)
    category_id = get_category_id(conn, category_hint) if category_hint else None

    extracted_model = extract_model(raw.title)

    params = {
        "source_id": source_id,
        "category_id": category_id,
        "source_post_id": raw.source_post_id,
        "title": raw.title[:500],
        "extracted_model": extracted_model,
        "price": raw.price,
        "shipping_fee": getattr(raw, "shipping_fee", 0) or 0,
        "currency": "KRW",
        "mall_url": raw.mall_url,
        "source_url": raw.source_url,
        "thumbnail_url": raw.thumbnail_url,
        "upvotes": raw.upvotes,
        "comments_count": raw.comments_count,
        "is_active": raw.is_active,
        "posted_at": raw.posted_at,
    }

    with conn.cursor() as cur:
        cur.execute(UPSERT_SQL, params)
        row = cur.fetchone()
        return row[0], row[1]


def run_pipeline(sources: Optional[list[str]] = None):
    """
    전체 크롤링 파이프라인 실행

    Args:
        sources: 실행할 소스 목록 (None이면 전체)
    """
    if sources is None:
        sources = ["뽐뿌", "클리앙", "펨코", "퀘이사존", "루리웹"]

    stats = {"inserted": 0, "updated": 0, "errors": 0}

    conn = get_connection()
    try:
        for source_name in sources:
            print(f"\n[파이프라인] {source_name} 크롤링 시작...")

            if source_name == "뽐뿌":
                raw_deals = ppomppu.crawl(pages=2)
            elif source_name == "클리앙":
                raw_deals = clien.crawl(pages=2)
            elif source_name == "펨코":
                raw_deals = fmkorea.crawl(pages=2)
            elif source_name == "퀘이사존":
                raw_deals = quasarzone.crawl(pages=2)
            elif source_name == "루리웹":
                raw_deals = ruliweb.crawl(pages=2)
            else:
                print(f"[파이프라인] 알 수 없는 소스: {source_name}")
                continue

            for raw in raw_deals:
                try:
                    deal_id, is_new = upsert_deal(conn, source_name, raw)
                    if is_new:
                        stats["inserted"] += 1
                    else:
                        stats["updated"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    print(f"[파이프라인] Upsert 오류 ({raw.title[:30]}): {e}")

            conn.commit()
            print(
                f"[파이프라인] {source_name} 완료 — "
                f"신규: {stats['inserted']}, 업데이트: {stats['updated']}, 오류: {stats['errors']}"
            )

    except Exception as e:
        conn.rollback()
        print(f"[파이프라인] 치명적 오류: {e}")
        raise
    finally:
        conn.close()

    return stats


if __name__ == "__main__":
    result = run_pipeline()
    print(f"\n전체 완료: {result}")
