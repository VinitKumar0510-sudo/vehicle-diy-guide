from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.knowledge_builder.agent import build_guide
from app.services.guide_session.intent import classify_intent

router = APIRouter()


class IntentRequest(BaseModel):
    query: str
    vehicle_desc: str = ""


class GuideRequest(BaseModel):
    make: str
    model: str
    year: int
    repair: str
    engine: str | None = None


@router.post("/intent")
async def detect_intent(req: IntentRequest):
    result = await classify_intent(req.query, req.vehicle_desc)
    return {
        "intent_type": result.intent_type,
        "repair_query": result.repair_query,
        "confidence": result.confidence,
        "diagnostic_needed": result.diagnostic_needed,
        "follow_up_questions": result.follow_up_questions,
    }


@router.post("/build")
async def build(req: GuideRequest):
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
