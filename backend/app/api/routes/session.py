import json
from dataclasses import asdict
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.services.guide_session.session import SessionState, chat
from app.services.knowledge_builder.synthesizer import SynthesizedGuide
from app.db.redis_client import get_redis

router = APIRouter()

SESSION_TTL = 60 * 60 * 24  # 24 hours


def _state_to_json(state: SessionState) -> str:
    return json.dumps({
        "guide": asdict(state.guide),
        "vehicle_desc": state.vehicle_desc,
        "current_step": state.current_step,
        "completed_steps": state.completed_steps,
        "conversation_history": state.conversation_history,
        "is_complete": state.is_complete,
    })


def _state_from_json(raw: str) -> SessionState:
    d = json.loads(raw)
    g = d["guide"]
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
    state = SessionState(guide=guide, vehicle_desc=d["vehicle_desc"])
    state.current_step = d["current_step"]
    state.completed_steps = d["completed_steps"]
    state.conversation_history = d["conversation_history"]
    state.is_complete = d["is_complete"]
    return state


async def _get_session(session_id: str) -> SessionState:
    redis = await get_redis()
    raw = await redis.get(f"session:{session_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return _state_from_json(raw)


async def _save_session(session_id: str, state: SessionState):
    redis = await get_redis()
    await redis.set(f"session:{session_id}", _state_to_json(state), ex=SESSION_TTL)


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
    state = SessionState(guide=guide, vehicle_desc=req.vehicle_desc)
    await _save_session(req.session_id, state)
    return {"ok": True, "total_steps": len(guide.steps)}


@router.post("/chat")
async def session_chat(req: ChatRequest):
    state = await _get_session(req.session_id)
    response = await chat(state, req.message)
    await _save_session(req.session_id, state)
    return {
        "message": response.message,
        "current_step": response.current_step,
        "total_steps": response.total_steps,
        "is_finished": response.is_finished,
        "safety_flag": response.safety_flag,
    }


@router.post("/next")
async def next_step(req: StepRequest):
    state = await _get_session(req.session_id)
    total = len(state.guide.steps)
    if state.current_step < total - 1:
        state.completed_steps.append(state.current_step)
        state.current_step += 1
    else:
        state.is_complete = True
        state.completed_steps.append(state.current_step)
    await _save_session(req.session_id, state)
    return {
        "current_step": state.current_step,
        "is_complete": state.is_complete,
    }


@router.get("/state/{session_id}")
async def get_state(session_id: str):
    state = await _get_session(session_id)
    return {
        "current_step": state.current_step,
        "completed_steps": state.completed_steps,
        "is_complete": state.is_complete,
        "total_steps": len(state.guide.steps),
    }
