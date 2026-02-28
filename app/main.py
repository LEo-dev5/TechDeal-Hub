from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api.deals import router as deals_router
from app.api.admin import router as admin_router
from app.core.config import settings


# ── 보안 헤더 미들웨어 ────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# ── FastAPI 앱 (프로덕션에서 Swagger 비활성화) ─────────────
limiter = Limiter(key_func=get_remote_address)

_DESCRIPTION = """
전자제품 핫딜 애그리게이터 API

**법적 고지**: 본 서비스는 비영리 목적으로 뽐뿌·클리앙·퀘이사존·루리웹의 공개 게시물을
링크·요약 형태로만 집약합니다. 모든 콘텐츠 저작권은 원저작자에게 귀속됩니다.
저작권 침해 신고: contact@techdeal-hub.local
"""

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=_DESCRIPTION,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-Admin-Key"],
)

app.include_router(deals_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"status": "ok", "version": settings.app_version}


@app.get("/health")
def health():
    return {"status": "healthy"}
