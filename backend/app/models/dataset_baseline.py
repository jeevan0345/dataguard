"""
DataGuard Dataset Baseline Model
Persists expected schema, bounded reference sample rows, and statistical summaries for a dataset
so that schema drift and distribution drift (KS-test) can be continuously evaluated on real uploads.
"""

from typing import Any, Optional
from sqlalchemy import Float, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class DatasetBaseline(Base):
    """
    Stores baseline expectation for a dataset.
    """

    __tablename__ = "dataset_baselines"

    dataset_path: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
        index=True,
    )

    expected_schema: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    reference_sample: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
    )

    numeric_summary: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    quality_score: Mapped[float] = mapped_column(
        Float,
        default=100.0,
    )

    sample_row_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
