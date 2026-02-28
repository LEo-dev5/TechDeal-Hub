from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.schemas import DealDetail, DealSummary, DealsResponse, StatsResponse
from app.core.database import get_db
from app.models.deal import Category, Deal, Source

router = APIRouter(prefix="/deals", tags=["deals"])
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=DealsResponse)
@limiter.limit("60/minute")
def get_deals(
    request: Request,
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=50, description="페이지 크기 (최대 50)"),
    category_id: Optional[int] = Query(None, description="카테고리 ID 필터"),
    source_id: Optional[int] = Query(None, description="소스 ID 필터"),
    active_only: bool = Query(True, description="진행중 핫딜만 조회"),
    keyword: Optional[str] = Query(None, max_length=100, description="제목/모델명 검색 (최대 100자)"),
    min_price: Optional[int] = Query(None, ge=0, description="최소 가격"),
    max_price: Optional[int] = Query(None, ge=0, description="최대 가격"),
    db: Session = Depends(get_db),
):
    """핫딜 목록 조회"""
    stmt = (
        select(Deal)
        .options(selectinload(Deal.source), selectinload(Deal.category))
        .order_by(Deal.posted_at.desc())
    )

    if active_only:
        stmt = stmt.where(Deal.is_active == True)
    if category_id:
        stmt = stmt.where(Deal.category_id == category_id)
    if source_id:
        stmt = stmt.where(Deal.source_id == source_id)
    if keyword:
        stmt = stmt.where(
            Deal.title.ilike(f"%{keyword}%") |
            Deal.extracted_model.ilike(f"%{keyword}%")
        )
    if min_price is not None:
        stmt = stmt.where(Deal.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Deal.price <= max_price)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.offset((page - 1) * size).limit(size)).all()

    return DealsResponse(total=total, page=page, size=size, items=items)


@router.get("/stats", response_model=StatsResponse)
@limiter.limit("30/minute")
def get_stats(request: Request, db: Session = Depends(get_db)):
    """통계 조회"""
    total_deals = db.scalar(select(func.count(Deal.id)))
    active_deals = db.scalar(select(func.count(Deal.id)).where(Deal.is_active == True))

    sources = db.execute(
        select(Source.name, func.count(Deal.id).label("count"))
        .join(Deal, Deal.source_id == Source.id)
        .group_by(Source.id)
    ).all()

    categories = db.execute(
        select(Category.name, func.count(Deal.id).label("count"))
        .join(Deal, Deal.category_id == Category.id)
        .group_by(Category.id)
        .order_by(func.count(Deal.id).desc())
    ).all()

    return StatsResponse(
        total_deals=total_deals or 0,
        active_deals=active_deals or 0,
        sources=[{"name": s.name, "count": s.count} for s in sources],
        categories=[{"name": c.name, "count": c.count} for c in categories],
    )


@router.get("/{deal_id}", response_model=DealDetail)
@limiter.limit("120/minute")
def get_deal(request: Request, deal_id: int, db: Session = Depends(get_db)):
    """딜 상세 조회"""
    deal = db.scalar(
        select(Deal)
        .where(Deal.id == deal_id)
        .options(selectinload(Deal.source), selectinload(Deal.category))
    )
    if not deal:
        raise HTTPException(status_code=404, detail="딜을 찾을 수 없습니다")
    return deal
