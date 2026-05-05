import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings
from app.db.connection import init_db
from app.db.redis_client import get_redis, close_redis
from app.api.routes import guides, session

logger = logging.getLogger(__name__)
settings = get_settings()
is_prod = settings.environment == "production"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await get_redis()
    yield
    await close_redis()


app = FastAPI(
    title="WrenchAI API",
    lifespan=lifespan,
    # Disable interactive docs in production
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,   # no cookies — credentials header was unnecessary
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(l) for l in e["loc"]), "msg": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"errors": errors})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred"},
    )


app.include_router(guides.router, prefix="/api/guides")
app.include_router(session.router, prefix="/api/session")


@app.get("/api/health")
async def health():
    components = {}
    overall = "ok"

    try:
        redis = await get_redis()
        await redis.ping()
        components["redis"] = "ok"
    except Exception:
        components["redis"] = "error"
        overall = "degraded"

    try:
        from app.db.connection import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await db.execute(__import__("sqlalchemy").text("SELECT 1"))
        components["postgres"] = "ok"
    except Exception:
        components["postgres"] = "error"
        overall = "degraded"

    return {"status": overall, "components": components}
