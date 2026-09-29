from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ETLRun(Base):
    """
    Stores information about one ETL pipeline execution.
    """

    pipeline_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    dataset_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="RUNNING",
        index=True
    )

    rows_input: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    rows_output: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    duration_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    checkpoint: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    findings: Mapped[list["ETLFinding"]] = relationship(
        "ETLFinding",
        back_populates="run",
        cascade="all, delete-orphan"
    )


class ETLFinding(Base):
    """
    Stores a structured finding generated from an ETL anomaly.
    """

    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("etlruns.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    metric: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    finding_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True
    )

    actual_value: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    expected_average: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    lower_bound: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    upper_bound: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    deviation: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    evidence: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    likely_area: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    run: Mapped["ETLRun"] = relationship(
        "ETLRun",
        back_populates="findings"
    )