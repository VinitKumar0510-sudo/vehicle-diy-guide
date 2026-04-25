import anthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.guide import RepairGuide
from app.services.knowledge_builder.synthesizer import SynthesizedGuide
from app.config import get_settings

settings = get_settings()


async def embed_text(text_input: str) -> list[float]:
    # Claude doesn't have a dedicated embeddings endpoint yet;
    # use a lightweight approach with the messages API to extract a summary,
    # then fall back to a simple hash-based placeholder until embeddings are available.
    # In production: swap this for text-embedding-3-small or a local model.
    try:
        import hashlib
        import struct
        # Deterministic 1536-dim float vector from text hash (placeholder)
        h = hashlib.sha256(text_input.encode()).digest()
        base = [struct.unpack("f", h[i % 32:i % 32 + 4])[0] for i in range(1536)]
        # Normalize
        magnitude = sum(x**2 for x in base) ** 0.5
        return [x / magnitude for x in base] if magnitude else base
    except Exception:
        return [0.0] * 1536


async def store_guide(
    db: AsyncSession,
    guide: SynthesizedGuide,
    make: str,
    model: str,
    year: int,
    repair: str,
    engine: str | None = None,
) -> RepairGuide:
    embed_input = f"{year} {make} {model} {repair} {guide.title} {guide.summary}"
    embedding = await embed_text(embed_input)

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
        embedding=embedding,
    )

    db.add(db_guide)
    await db.commit()
    await db.refresh(db_guide)
    return db_guide


async def semantic_search(
    db: AsyncSession,
    query: str,
    make: str | None = None,
    model: str | None = None,
    limit: int = 5,
) -> list[RepairGuide]:
    embedding = await embed_text(query)

    stmt = select(RepairGuide)
    if make:
        stmt = stmt.where(RepairGuide.make.ilike(make))
    if model:
        stmt = stmt.where(RepairGuide.model.ilike(model))

    # pgvector cosine similarity
    stmt = stmt.order_by(
        RepairGuide.embedding.cosine_distance(embedding)
    ).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


def _infer_system(repair: str) -> str:
    repair_lower = repair.lower()
    system_keywords = {
        "brake": "brakes",
        "oil": "engine_lubrication",
        "filter": "filtration",
        "spark plug": "ignition",
        "battery": "electrical",
        "tire": "wheels_tires",
        "suspension": "suspension",
        "steering": "steering",
        "transmission": "drivetrain",
        "coolant": "cooling",
        "timing": "engine_timing",
        "alternator": "electrical",
        "starter": "electrical",
    }
    for keyword, system in system_keywords.items():
        if keyword in repair_lower:
            return system
    return "general"
