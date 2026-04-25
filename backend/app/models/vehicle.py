from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.connection import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    make: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)
    trim: Mapped[str | None] = mapped_column(String(200), nullable=True)
    engine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True, unique=True)
    specs: Mapped[dict | None] = mapped_column(JSON, nullable=True)
