import json
import anthropic
from dataclasses import dataclass
from typing import Optional
from app.config import get_settings
from app.services.knowledge_builder.sources.youtube import VideoSource
from app.services.knowledge_builder.sources.reddit import RedditPost
from app.services.knowledge_builder.sources.web import WebSource

settings = get_settings()

SAFETY_TIERS = {
    "brakes": "red",
    "brake": "red",
    "steering": "red",
    "suspension": "red",
    "wheel bearing": "red",
    "tie rod": "red",
    "ball joint": "red",
    "oil change": "yellow",
    "battery": "yellow",
    "filter": "yellow",
    "spark plug": "yellow",
    "timing": "yellow",
    "transmission": "yellow",
    "wiper": "green",
    "bulb": "green",
    "cabin filter": "green",
    "air filter": "green",
}


@dataclass
class SynthesizedGuide:
    title: str
    summary: str
    steps: list[dict]
    tools_required: list[str]
    parts_required: list[dict]
    difficulty: int
    time_estimate_minutes: int
    safety_tier: str
    confidence_score: float
    sources: list[str]
    warnings: list[str]


def _determine_safety_tier(repair: str) -> str:
    repair_lower = repair.lower()
    for keyword, tier in SAFETY_TIERS.items():
        if keyword in repair_lower:
            return tier
    return "yellow"


def _build_synthesis_prompt(
    make: str,
    model: str,
    year: int,
    engine: Optional[str],
    repair: str,
    web_sources: list[WebSource],
    video_sources: list[VideoSource],
    reddit_posts: list[RedditPost],
) -> str:
    context_parts = []

    if web_sources:
        context_parts.append("## Web Repair Guides\n")
        for i, src in enumerate(web_sources[:4], 1):
            context_parts.append(f"### Source {i}: {src.title} ({src.domain})\n{src.content}\n")

    if video_sources:
        context_parts.append("\n## YouTube Video Transcripts\n")
        for i, vid in enumerate(video_sources[:3], 1):
            excerpt = vid.transcript[:2500]
            context_parts.append(f"### Video {i}: {vid.title} ({vid.channel})\n{excerpt}\n")

    if reddit_posts:
        context_parts.append("\n## Community Knowledge (Reddit)\n")
        for i, post in enumerate(reddit_posts[:4], 1):
            comments = "\n".join(f"- {c}" for c in post.top_comments[:2])
            context_parts.append(
                f"### r/{post.subreddit}: {post.title}\n{post.body[:500]}\nTop comments:\n{comments}\n"
            )

    context = "\n".join(context_parts) if context_parts else "No external sources available."

    vehicle_desc = f"{year} {make} {model}"
    if engine:
        vehicle_desc += f" ({engine})"

    return f"""You are an expert automotive technician creating a precise, accurate repair guide.

Vehicle: {vehicle_desc}
Repair: {repair}

SOURCE MATERIAL:
{context}

Create a complete repair guide synthesized from these sources. Be specific to the {vehicle_desc}.

CRITICAL RULES:
- Torque specs and fluid capacities must be verified across multiple sources before including. If sources conflict, note both values and flag uncertainty.
- Include ONLY steps that are verified by at least one source. Do not invent steps.
- Flag any step where sources disagree with a note in the step.
- Factory service manual values take priority over forum/video values for specs.

Return ONLY valid JSON matching this exact schema:
{{
  "title": "string - descriptive title including vehicle and repair",
  "summary": "string - 2-3 sentence overview of what this repair involves",
  "difficulty": <1-5 integer, 1=beginner, 5=expert>,
  "time_estimate_minutes": <realistic integer>,
  "warnings": ["string - safety warnings, one per item"],
  "tools_required": ["string - specific tool name"],
  "parts_required": [
    {{
      "name": "string",
      "part_number": "string or null",
      "quantity": <integer>,
      "consumable": <boolean>,
      "notes": "string or null"
    }}
  ],
  "steps": [
    {{
      "step_number": <integer>,
      "title": "string - short action title",
      "instruction": "string - detailed what to do",
      "why": "string - brief reason this step matters",
      "torque_spec": "string or null - e.g. '79 ft-lbs'",
      "tool_needed": "string or null",
      "warning": "string or null - step-specific caution",
      "confidence": <0.0-1.0 float for this step>
    }}
  ],
  "sources_used": ["string - URL or description of source"],
  "overall_confidence": <0.0-1.0 float>,
  "confidence_notes": "string - explain what drove confidence score up or down"
}}"""


async def synthesize_guide(
    make: str,
    model: str,
    year: int,
    repair: str,
    engine: Optional[str] = None,
    web_sources: Optional[list[WebSource]] = None,
    video_sources: Optional[list[VideoSource]] = None,
    reddit_posts: Optional[list[RedditPost]] = None,
) -> Optional[SynthesizedGuide]:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    prompt = _build_synthesis_prompt(
        make=make,
        model=model,
        year=year,
        engine=engine,
        repair=repair,
        web_sources=web_sources or [],
        video_sources=video_sources or [],
        reddit_posts=reddit_posts or [],
    )

    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=8192,
        system="You are an expert automotive technician. Return only valid JSON. No markdown fences, no explanation, no commentary. Start your response with { and end with }.",
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try extracting JSON from markdown block if model wrapped it
        import re
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
        else:
            return None

    safety_tier = _determine_safety_tier(repair)

    all_sources = [s.url for s in (web_sources or [])] + \
                  [v.url for v in (video_sources or [])] + \
                  [p.url for p in (reddit_posts or [])]

    return SynthesizedGuide(
        title=data["title"],
        summary=data["summary"],
        steps=data["steps"],
        tools_required=data["tools_required"],
        parts_required=data["parts_required"],
        difficulty=data["difficulty"],
        time_estimate_minutes=data["time_estimate_minutes"],
        safety_tier=safety_tier,
        confidence_score=data["overall_confidence"],
        sources=all_sources,
        warnings=data.get("warnings", []),
    )
