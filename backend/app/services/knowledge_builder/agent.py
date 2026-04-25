import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from app.services.knowledge_builder.sources.youtube import search_repair_videos
from app.services.knowledge_builder.sources.reddit import fetch_repair_posts
from app.services.knowledge_builder.sources.web import search_repair_guides
from app.services.knowledge_builder.sources.images import fetch_step_images
from app.services.knowledge_builder.synthesizer import synthesize_guide, SynthesizedGuide

logger = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.65


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


async def build_guide(
    make: str,
    model: str,
    year: int,
    repair: str,
    engine: Optional[str] = None,
) -> KnowledgeBuildResult:
    logger.info(f"Building guide: {year} {make} {model} — {repair}")

    web_task = search_repair_guides(make, model, year, repair)
    video_task = search_repair_videos(make, model, year, repair)
    reddit_task = fetch_repair_posts(make, model, year, repair)

    results = await asyncio.gather(web_task, video_task, reddit_task, return_exceptions=True)
    web_sources   = results[0] if not isinstance(results[0], Exception) else []
    video_sources = results[1] if not isinstance(results[1], Exception) else []
    reddit_posts  = results[2] if not isinstance(results[2], Exception) else []

    logger.info(
        f"Sources gathered: {len(web_sources)} web, {len(video_sources)} videos, {len(reddit_posts)} reddit posts"
    )

    guide = await synthesize_guide(
        make=make,
        model=model,
        year=year,
        repair=repair,
        engine=engine,
        web_sources=web_sources,
        video_sources=video_sources,
        reddit_posts=reddit_posts,
    )

    needs_review = guide is None or guide.confidence_score < LOW_CONFIDENCE_THRESHOLD

    if guide and needs_review:
        logger.warning(
            f"Low confidence ({guide.confidence_score:.2f}) for {year} {make} {model} — {repair}. Flagging for review."
        )

    # Attach images to each step
    if guide:
        video_ids = [v.video_id for v in video_sources]
        for step in guide.steps:
            imgs = await fetch_step_images(
                make=make, model=model, year=year,
                repair=repair, step_title=step["title"],
                video_ids=video_ids,
            )
            step["images"] = [{"url": i.url, "caption": i.caption} for i in imgs]

    return KnowledgeBuildResult(
        guide=guide,
        make=make,
        model=model,
        year=year,
        repair=repair,
        engine=engine,
        needs_human_review=needs_review,
        source_counts={
            "web": len(web_sources),
            "video": len(video_sources),
            "reddit": len(reddit_posts),
        },
    )
