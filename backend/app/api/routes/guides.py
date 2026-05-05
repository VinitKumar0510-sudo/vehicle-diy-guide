from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services.knowledge_builder.agent import build_guide
from app.services.guide_session.intent import classify_intent

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class IntentRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    vehicle_desc: str = Field(default="", max_length=200)


class GuideRequest(BaseModel):
    make: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1885, le=2030)
    repair: str = Field(..., min_length=1, max_length=300)
    engine: str | None = Field(default=None, max_length=100)


@router.post("/intent")
@limiter.limit("30/hour")
async def detect_intent(request: Request, req: IntentRequest):
    result = await classify_intent(req.query, req.vehicle_desc)
    return {
        "intent_type": result.intent_type,
        "repair_query": result.repair_query,
        "confidence": result.confidence,
        "diagnostic_needed": result.diagnostic_needed,
        "follow_up_questions": result.follow_up_questions,
    }


@router.post("/build")
@limiter.limit("10/hour")
async def build(request: Request, req: GuideRequest):
    result = await build_guide(
        make=req.make,
        model=req.model,
        year=req.year,
        repair=req.repair,
        engine=req.engine,
    )
    if not result.guide:
        raise HTTPException(status_code=422, detail="Could not synthesize guide")

    guide = result.guide
    return {
        "title": guide.title,
        "summary": guide.summary,
        "difficulty": guide.difficulty,
        "time_estimate_minutes": guide.time_estimate_minutes,
        "safety_tier": guide.safety_tier,
        "confidence_score": guide.confidence_score,
        "warnings": guide.warnings,
        "tools_required": guide.tools_required,
        "parts_required": guide.parts_required,
        "steps": guide.steps,
        "from_cache": result.from_cache,
        "source_counts": result.source_counts,
    }
