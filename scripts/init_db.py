"""
DB 초기화 스크립트
실행: python -m scripts.init_db
"""
import os
import psycopg2
from pathlib import Path

DB_URL = os.environ["DATABASE_URL"]  # 기본값 없음 — .env 설정 필수


def init_db():
    sql_path = Path(__file__).parent / "init_schema.sql"
    sql = sql_path.read_text(encoding="utf-8")

    conn = psycopg2.connect(DB_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("✅ DB 스키마 초기화 완료")
    except Exception as e:
        conn.rollback()
        print(f"❌ 오류: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
