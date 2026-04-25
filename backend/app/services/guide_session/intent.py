import anthropic
import json
from dataclasses import dataclass
from enum import Enum
from app.config import get_settings

settings = get_settings()


class IntentType(str, Enum):
    SYMPTOM = "symptom"
    SPECIFIC_REPAIR = "specific_repair"
    MAINTENANCE = "maintenance"
    QUESTION = "question"


@dataclass
class ClassifiedIntent:
    intent_type: IntentType
    repair_query: str | None
    confidence: float
    diagnostic_needed: bool
    follow_up_questions: list[str]


INTENT_SYSTEM = """You are an automotive intent classifier. Classify what a user wants into exactly one category:

- symptom: User describes a problem/symptom but doesn't know the repair (e.g. "my brakes are squealing", "engine light is on")
- specific_repair: User knows the exact repair they want to do (e.g. "change brake pads", "replace battery")
- maintenance: User asks about scheduled maintenance (e.g. "what's due on my car", "when do I change oil")
- question: User asks a general knowledge question (e.g. "how does a caliper work", "what is synthetic oil")

Return only valid JSON:
{
  "intent_type": "symptom|specific_repair|maintenance|question",
  "repair_query": "normalized repair name, or null if symptom/maintenance/question",
  "confidence": 0.0-1.0,
  "diagnostic_needed": true/false,
  "follow_up_questions": ["question 1", "question 2"] (only if symptom, max 3 targeted questions to narrow diagnosis)
}"""


async def classify_intent(user_input: str, vehicle_context: str = "") -> ClassifiedIntent:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    context = f"Vehicle: {vehicle_context}\n" if vehicle_context else ""
    prompt = f"{context}User said: \"{user_input}\""

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=512,
        system=INTENT_SYSTEM + "\n\nCRITICAL: Return raw JSON only. No markdown fences, no explanation. Start with { and end with }.",
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        raw = match.group(0) if match else raw

    data = json.loads(raw)

    return ClassifiedIntent(
        intent_type=IntentType(data["intent_type"]),
        repair_query=data.get("repair_query"),
        confidence=data["confidence"],
        diagnostic_needed=data["diagnostic_needed"],
        follow_up_questions=data.get("follow_up_questions", []),
    )
