from fastapi import APIRouter
from pydantic import BaseModel
from app.services.guide_session.session import SessionState, chat
from app.services.knowledge_builder.synthesizer import SynthesizedGuide

router = APIRouter()

# In-memory session store — Redis in production
_sessions: dict[str, SessionState] = {}


class StartSessionRequest(BaseModel):
    session_id: str
    guide: dict
    vehicle_desc: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class StepRequest(BaseModel):
    session_id: str


@router.post("/start")
async def start_session(req: StartSessionRequest):
    g = req.guide
    guide = SynthesizedGuide(
        title=g["title"],
        summary=g["summary"],
        steps=g["steps"],
        tools_required=g["tools_required"],
        parts_required=g["parts_required"],
        difficulty=g["difficulty"],
        time_estimate_minutes=g["time_estimate_minutes"],
        safety_tier=g["safety_tier"],
        confidence_score=g["confidence_score"],
        sources=g.get("sources", []),
        warnings=g.get("warnings", []),
    )
    _sessions[req.session_id] = SessionState(
        guide=guide,
        vehicle_desc=req.vehicle_desc,
    )
    return {"ok": True, "total_steps": len(guide.steps)}


@router.post("/chat")
async def session_chat(req: ChatRequest):
    state = _sessions.get(req.session_id)
    if not state:
        return {"error": "Session not found"}
    response = await chat(state, req.message)
    return {
        "message": response.message,
        "current_step": response.current_step,
        "total_steps": response.total_steps,
        "is_finished": response.is_finished,
        "safety_flag": response.safety_flag,
    }


@router.post("/next")
async def next_step(req: StepRequest):
    state = _sessions.get(req.session_id)
    if not state:
        return {"error": "Session not found"}
    total = len(state.guide.steps)
    if state.current_step < total - 1:
        state.completed_steps.append(state.current_step)
        state.current_step += 1
    else:
        state.is_complete = True
        state.completed_steps.append(state.current_step)
    return {
        "current_step": state.current_step,
        "is_complete": state.is_complete,
    }


@router.get("/state/{session_id}")
async def get_state(session_id: str):
    state = _sessions.get(session_id)
    if not state:
        return {"error": "Session not found"}
    return {
        "current_step": state.current_step,
        "completed_steps": state.completed_steps,
        "is_complete": state.is_complete,
        "total_steps": len(state.guide.steps),
    }
