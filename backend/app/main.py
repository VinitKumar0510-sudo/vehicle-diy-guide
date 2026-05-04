from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import get_settings
from app.db.connection import init_db
from app.db.redis_client import get_redis, close_redis
from app.api.routes import guides, session

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await get_redis()  # warm up connection
    yield
    await close_redis()


app = FastAPI(title="WrenchAI API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(guides.router, prefix="/api/guides")
app.include_router(session.router, prefix="/api/session")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
