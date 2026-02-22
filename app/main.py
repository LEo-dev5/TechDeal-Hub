from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deals import router as deals_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="전자제품 핫딜 애그리게이터 API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deals_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"status": "ok", "version": settings.app_version}


@app.get("/health")
def health():
    return {"status": "healthy"}
