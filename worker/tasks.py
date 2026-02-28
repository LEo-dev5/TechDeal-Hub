"""
Celery 태스크 정의
"""
import os
from datetime import datetime, timedelta

import psycopg2

from worker.celery_app import app

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://techdeal:changeme@localhost:5432/techdeal")


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def crawl_source(self, source_name: str):
    """
    특정 소스 크롤링 태스크

    Args:
        source_name: 크롤링할 소스명 ('뽐뿌', '클리앙' 등)
    """
    try:
        from scraper.pipeline import run_pipeline
        stats = run_pipeline(sources=[source_name])
        return {
            "source": source_name,
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
        }
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, max_retries=2)
def crawl_all(self):
    """전체 소스 크롤링 태스크"""
    try:
        from scraper.pipeline import run_pipeline
        stats = run_pipeline()
        return {
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
        }
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task
def cleanup_expired_deals():
    """
    30일 이상 지난 비활성 딜 정리
    (실제 삭제 대신 is_active=FALSE 상태 유지, 오래된 것만 정리)
    """
    cutoff = datetime.now() - timedelta(days=30)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE deals
                SET is_active = FALSE
                WHERE posted_at < %s AND is_active = TRUE
                """,
                (cutoff,),
            )
            affected = cur.rowcount
        conn.commit()
        return {"cleaned": affected, "cutoff": cutoff.isoformat()}
    finally:
        conn.close()


@app.task
def trigger_crawl(source_name: str):
    """수동 크롤링 트리거 (API에서 호출용)"""
    return crawl_source.delay(source_name)
