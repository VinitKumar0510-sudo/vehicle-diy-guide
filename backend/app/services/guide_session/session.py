import anthropic
import json
from dataclasses import dataclass, field
from app.config import get_settings
from app.services.knowledge_builder.synthesizer import SynthesizedGuide

settings = get_settings()


@dataclass
class SessionState:
    guide: SynthesizedGuide
    vehicle_desc: str
    current_step: int = 0
    completed_steps: list[int] = field(default_factory=list)
    conversation_history: list[dict] = field(default_factory=list)
    is_complete: bool = False


@dataclass
class SessionResponse:
    message: str
    current_step: int
    total_steps: int
    step_complete: bool
    is_finished: bool
    safety_flag: bool = False


GUIDE_SESSION_SYSTEM = """You are a skilled mechanic guiding someone through a car repair in real time. You know their exact vehicle and exactly which step they are on.

Rules:
- Be conversational, calm, and encouraging. They may be nervous.
- Answer questions directly and specifically — never say "refer to the manual."
- If you detect confusion or a safety issue, flag it immediately.
- Keep responses SHORT. One clear action or answer per response.
- If they describe something that sounds wrong or dangerous, say so directly.
- You have full context of the guide — reference specific part names, bolt locations, torque specs.
- Never make up specs not in the guide. If you don't know, say so and tell them to verify."""


def _build_session_context(state: SessionState) -> str:
    guide = state.guide
    current = guide.steps[state.current_step] if state.current_step < len(guide.steps) else None

    context = f"""VEHICLE: {state.vehicle_desc}
REPAIR: {guide.title}
TOTAL STEPS: {len(guide.steps)}
CURRENT STEP: {state.current_step + 1} of {len(guide.steps)}
SAFETY TIER: {guide.safety_tier.upper()}

CURRENT STEP DETAIL:
{json.dumps(current, indent=2) if current else "Repair complete"}

ALL STEPS SUMMARY:
{chr(10).join(f"Step {s['step_number']}: {s['title']}" for s in guide.steps)}

TOOLS FOR THIS JOB: {', '.join(guide.tools_required)}
WARNINGS: {'; '.join(guide.warnings[:3])}"""

    return context


async def chat(state: SessionState, user_message: str) -> SessionResponse:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    guide_context = _build_session_context(state)
    state.conversation_history.append({"role": "user", "content": user_message})

    messages = [
        {"role": "user", "content": f"GUIDE CONTEXT:\n{guide_context}\n\nBEGIN SESSION"},
        {"role": "assistant", "content": f"I'm here to guide you through the {state.guide.title} on your {state.vehicle_desc}. We're on Step {state.current_step + 1}: {state.guide.steps[state.current_step]['title'] if state.current_step < len(state.guide.steps) else 'completion'}. What do you need?"},
    ] + state.conversation_history

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system=GUIDE_SESSION_SYSTEM,
        messages=messages,
    )

    reply = response.content[0].text.strip()
    state.conversation_history.append({"role": "assistant", "content": reply})

    safety_keywords = ["stop", "danger", "do not drive", "professional", "unsafe", "immediately"]
    safety_flag = any(kw in reply.lower() for kw in safety_keywords)

    step_advanced = _check_step_advance(user_message)
    if step_advanced and state.current_step < len(state.guide.steps) - 1:
        state.completed_steps.append(state.current_step)
        state.current_step += 1
    elif step_advanced and state.current_step == len(state.guide.steps) - 1:
        state.is_complete = True
        state.completed_steps.append(state.current_step)

    return SessionResponse(
        message=reply,
        current_step=state.current_step + 1,
        total_steps=len(state.guide.steps),
        step_complete=step_advanced,
        is_finished=state.is_complete,
        safety_flag=safety_flag,
    )


def _check_step_advance(message: str) -> bool:
    advance_phrases = [
        "done", "complete", "finished", "next step", "next",
        "got it", "mark complete", "did it", "moved on", "ready"
    ]
    return any(phrase in message.lower() for phrase in advance_phrases)
