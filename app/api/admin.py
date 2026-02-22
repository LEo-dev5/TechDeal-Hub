"""
관리자 엔드포인트 (크롤링 수동 트리거 등)
"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/crawl/{source_name}")
def trigger_crawl(source_name: str):
    """특정 소스 크롤링 수동 트리거"""
    from worker.tasks import crawl_source
    task = crawl_source.delay(source_name)
    return {"task_id": task.id, "source": source_name, "status": "queued"}


@router.post("/crawl")
def trigger_crawl_all():
    """전체 소스 크롤링 수동 트리거"""
    from worker.tasks import crawl_all
    task = crawl_all.delay()
    return {"task_id": task.id, "status": "queued"}
