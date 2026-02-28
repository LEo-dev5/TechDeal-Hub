"""
관리자 엔드포인트 (크롤링 수동 트리거 등)
"""
import os
import secrets
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

router = APIRouter(prefix="/admin", tags=["admin"])

# ── API Key 인증 ────────────────────────────────────────────
_API_KEY_HEADER = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def verify_admin_key(api_key: str = Security(_API_KEY_HEADER)) -> str:
    expected = os.getenv("ADMIN_API_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="ADMIN_API_KEY 환경변수가 설정되지 않았습니다")
    if not secrets.compare_digest(api_key or "", expected):
        raise HTTPException(status_code=403, detail="관리자 권한이 없습니다")
    return api_key


# ── 허용 소스 목록 (Enum으로 강제) ────────────────────────
class SourceName(str, Enum):
    ppomppu    = "뽐뿌"
    clien      = "클리앙"
    quasarzone = "퀘이사존"
    ruliweb    = "루리웹"


# ── 엔드포인트 ────────────────────────────────────────────
@router.post("/crawl/{source_name}")
def trigger_crawl(
    source_name: SourceName,
    _: str = Depends(verify_admin_key),
):
    """특정 소스 크롤링 수동 트리거 (Admin Key 필요)"""
    from worker.tasks import crawl_source
    task = crawl_source.delay(source_name.value)
    return {"task_id": task.id, "source": source_name.value, "status": "queued"}


@router.post("/crawl")
def trigger_crawl_all(_: str = Depends(verify_admin_key)):
    """전체 소스 크롤링 수동 트리거 (Admin Key 필요)"""
    from worker.tasks import crawl_all
    task = crawl_all.delay()
    return {"task_id": task.id, "status": "queued"}
