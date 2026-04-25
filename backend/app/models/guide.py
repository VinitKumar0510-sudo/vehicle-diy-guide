from sqlalchemy import String, Integer, Float, JSON, Text, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.db.connection import Base


class RepairGuide(Base):
    __tablename__ = "repair_guides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    make: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    year_start: Mapped[int] = mapped_column(Integer)
    year_end: Mapped[int] = mapped_column(Integer)
    engine: Mapped[str | None] = mapped_column(String(100), nullable=True)

    repair_type: Mapped[str] = mapped_column(String(200))
    system: Mapped[str] = mapped_column(String(100))

    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text)
    steps: Mapped[list] = mapped_column(JSON)
    tools_required: Mapped[list] = mapped_column(JSON)
    parts_required: Mapped[list] = mapped_column(JSON)

    difficulty: Mapped[int] = mapped_column(Integer)   # 1-5
    time_estimate_minutes: Mapped[int] = mapped_column(Integer)
    safety_tier: Mapped[str] = mapped_column(String(10))  # green/yellow/red

    confidence_score: Mapped[float] = mapped_column(Float)
    sources: Mapped[list] = mapped_column(JSON)

    community_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)

    embedding: Mapped[list | None] = mapped_column(Vector(1536), nullable=True)
