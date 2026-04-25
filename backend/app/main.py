from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.connection import init_db
from app.api.routes import guides, session


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Vehicle DIY Guide API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(guides.router, prefix="/api/guides")
app.include_router(session.router, prefix="/api/session")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
