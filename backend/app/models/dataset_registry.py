from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DatasetRegistry(Base):

    __tablename__ = "dataset_registry"

    dataset_name: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False
    )

    dataset_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    file_format: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    row_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    column_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    quality_score: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="Registered"
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    last_profiled_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )