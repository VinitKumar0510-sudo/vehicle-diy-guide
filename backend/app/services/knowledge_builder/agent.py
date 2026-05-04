import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from app.services.knowledge_builder.sources.youtube import search_repair_videos
from app.services.knowledge_builder.sources.reddit import fetch_repair_posts
from app.services.knowledge_builder.sources.web import search_repair_guides
from app.services.knowledge_builder.synthesizer import synthesize_guide, SynthesizedGuide
from app.config import get_settings

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.65

# Simple repairs: well-documented, low-risk, short guides — Haiku is sufficient
_SIMPLE_REPAIRS = {
    "wiper blade replacement",
    "air filter replacement",
    "cabin air filter replacement",
    "battery replacement",
}


def _pick_model(repair: str) -> str:
    """Use Haiku for simple repairs, Sonnet for everything else."""
    settings = get_settings()
    if repair.lower().strip() in _SIMPLE_REPAIRS:
        logger.info(f"Using Haiku for simple repair: {repair}")
        return settings.claude_chat_model   # Haiku
    return settings.claude_model            # Sonnet


@dataclass
class KnowledgeBuildResult:
    guide: Optional[SynthesizedGuide]
    make: str
    model: str
    year: int
    repair: str
    engine: Optional[str]
    needs_human_review: bool
    source_counts: dict
    from_cache: bool = False


async def build_guide(
    make: str,
    model: str,
    year: int,
    repair: str,
    engine: Optional[str] = None,
) -> KnowledgeBuildResult:
    # Check DB cache first — only synthesize if we haven't built this before
    try:
        from app.db.connection import AsyncSessionLocal
        from app.db.guide_repo import find_guide, save_guide, db_guide_to_synthesized
        async with AsyncSessionLocal() as db:
            cached = await find_guide(db, make, model, year, repair)
        if cached:
            logger.info(f"Cache hit: {year} {make} {model} — {repair} (guide #{cached.id})")
            return KnowledgeBuildResult(
                guide=db_guide_to_synthesized(cached),
                make=make, model=model, year=year,
                repair=repair, engine=engine,
                needs_human_review=cached.confidence_score < LOW_CONFIDENCE_THRESHOLD,
                source_counts={"web": 0, "video": 0, "reddit": 0},
                from_cache=True,
            )
    except Exception as e:
        logger.warning(f"DB cache lookup failed, building fresh: {e}")

    logger.info(f"Building guide: {year} {make} {model} — {repair}")

    web_task    = search_repair_guides(make, model, year, repair)
    video_task  = search_repair_videos(make, model, year, repair)
    reddit_task = fetch_repair_posts(make, model, year, repair)

    results = await asyncio.gather(web_task, video_task, reddit_task, return_exceptions=True)
    web_sources   = results[0] if not isinstance(results[0], Exception) else []
    video_sources = results[1] if not isinstance(results[1], Exception) else []
    reddit_posts  = results[2] if not isinstance(results[2], Exception) else []

    logger.info(
        f"Sources: {len(web_sources)} web, {len(video_sources)} videos, {len(reddit_posts)} reddit"
    )

    model_id = _pick_model(repair)
    guide = await synthesize_guide(
        make=make, model=model, year=year, repair=repair, engine=engine,
        web_sources=web_sources, video_sources=video_sources, reddit_posts=reddit_posts,
        model_id=model_id,
    )

    needs_review = guide is None or guide.confidence_score < LOW_CONFIDENCE_THRESHOLD

    if guide and needs_review:
        logger.warning(
            f"Low confidence ({guide.confidence_score:.2f}) for {year} {make} {model} — {repair}"
        )

    # Save to DB so next user gets it instantly.
    # Always save if confidence >= 0.3 — low-confidence guides still have valid steps,
    # they just need the "verify spec" warning shown on screen. Saves re-hitting the API
    # on every pre-builder run.
    if guide and guide.confidence_score >= 0.3:
        try:
            from app.db.connection import AsyncSessionLocal
            from app.db.guide_repo import save_guide
            async with AsyncSessionLocal() as db:
                await save_guide(db, guide, make, model, year, repair, engine)
        except Exception as e:
            logger.warning(f"Failed to save guide to DB: {e}")

    return KnowledgeBuildResult(
        guide=guide,
        make=make, model=model, year=year,
        repair=repair, engine=engine,
        needs_human_review=needs_review,
        source_counts={
            "web": len(web_sources),
            "video": len(video_sources),
            "reddit": len(reddit_posts),
        },
        from_cache=False,
    )
