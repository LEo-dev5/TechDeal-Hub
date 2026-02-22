from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SourceSchema(BaseModel):
    id: int
    name: str
    base_url: str

    class Config:
        from_attributes = True


class CategorySchema(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True


class DealSummary(BaseModel):
    """목록 조회용 요약 스키마"""
    id: int
    title: str
    extracted_model: Optional[str]
    price: Optional[int]
    shipping_fee: int
    currency: str
    source_url: str
    mall_url: Optional[str]
    thumbnail_url: Optional[str]
    upvotes: int
    comments_count: int
    is_active: bool
    posted_at: datetime
    source: SourceSchema
    category: Optional[CategorySchema] = None

    class Config:
        from_attributes = True


class DealDetail(DealSummary):
    """상세 조회용 스키마"""
    original_price: Optional[int]
    scraped_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DealsResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list[DealSummary]


class StatsResponse(BaseModel):
    total_deals: int
    active_deals: int
    sources: list[dict]
    categories: list[dict]
