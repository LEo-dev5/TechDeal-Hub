"""
Celery 앱 설정
"""
import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "techdeal",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["worker.tasks"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    # 태스크 재시도 설정
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # 결과 만료 (24시간)
    result_expires=86400,
)

# 주기적 크롤링 스케줄
app.conf.beat_schedule = {
    # 뽐뿌: 10분마다 크롤링
    "crawl-ppomppu-every-10min": {
        "task": "worker.tasks.crawl_source",
        "schedule": crontab(minute="*/10"),
        "args": ("뽐뿌",),
    },
    # 클리앙: 15분마다 크롤링
    "crawl-clien-every-15min": {
        "task": "worker.tasks.crawl_source",
        "schedule": crontab(minute="*/15"),
        "args": ("클리앙",),
    },
    # 품절 정리: 매일 새벽 4시
    "cleanup-expired-deals": {
        "task": "worker.tasks.cleanup_expired_deals",
        "schedule": crontab(hour=4, minute=0),
    },
}
