import json
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.guide import RepairGuide
from app.services.knowledge_builder.synthesizer import SynthesizedGuide

logger = logging.getLogger(__name__)


async def find_guide(
    db: AsyncSession,
    make: str,
    model: str,
    year: int,
    repair: str,
) -> RepairGuide | None:
    vehicle_filters = and_(
        RepairGuide.make.ilike(make),
        RepairGuide.model.ilike(model),
        RepairGuide.year_start <= year,
        RepairGuide.year_end >= year,
    )

    # Stage 1: exact repair string match
    stmt = select(RepairGuide).where(
        and_(vehicle_filters, RepairGuide.repair_type.ilike(repair))
    ).order_by(RepairGuide.confidence_score.desc()).limit(1)
    result = await db.execute(stmt)
    hit = result.scalar_one_or_none()
    if hit:
        return hit

    # Stage 2: same vehicle + same repair system (handles non-deterministic intent)
    system = _infer_system(repair)
    if system != "general":
        stmt = select(RepairGuide).where(
            and_(vehicle_filters, RepairGuide.system == system)
        ).order_by(RepairGuide.confidence_score.desc()).limit(1)
        result = await db.execute(stmt)
        hit = result.scalar_one_or_none()
        if hit:
            logger.info(f"Cache hit via system fallback ({system}): {hit.title}")
            return hit

    return None


async def save_guide(
    db: AsyncSession,
    guide: SynthesizedGuide,
    make: str,
    model: str,
    year: int,
    repair: str,
    engine: str | None = None,
) -> RepairGuide:
    db_guide = RepairGuide(
        make=make,
        model=model,
        year_start=year,
        year_end=year,
        engine=engine,
        repair_type=repair,
        system=_infer_system(repair),
        title=guide.title,
        summary=guide.summary,
        steps=guide.steps,
        tools_required=guide.tools_required,
        parts_required=guide.parts_required,
        difficulty=guide.difficulty,
        time_estimate_minutes=guide.time_estimate_minutes,
        safety_tier=guide.safety_tier,
        confidence_score=guide.confidence_score,
        sources=guide.sources,
        warnings=guide.warnings,
    )
    db.add(db_guide)
    await db.commit()
    await db.refresh(db_guide)
    logger.info(f"Saved guide #{db_guide.id}: {db_guide.title}")
    return db_guide


def db_guide_to_synthesized(db_guide: RepairGuide) -> SynthesizedGuide:
    return SynthesizedGuide(
        title=db_guide.title,
        summary=db_guide.summary,
        steps=db_guide.steps,
        tools_required=db_guide.tools_required,
        parts_required=db_guide.parts_required,
        difficulty=db_guide.difficulty,
        time_estimate_minutes=db_guide.time_estimate_minutes,
        safety_tier=db_guide.safety_tier,
        confidence_score=db_guide.confidence_score,
        sources=db_guide.sources,
        warnings=db_guide.warnings or [],
    )


def _infer_system(repair: str) -> str:
    repair_lower = repair.lower()
    mapping = {
        "brake": "brakes", "oil": "engine_lubrication",
        "filter": "filtration", "spark plug": "ignition",
        "battery": "electrical", "tire": "wheels_tires",
        "suspension": "suspension", "steering": "steering",
        "transmission": "drivetrain", "coolant": "cooling",
        "timing": "engine_timing", "alternator": "electrical",
    }
    for keyword, system in mapping.items():
        if keyword in repair_lower:
            return system
    return "general"
