from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class InspectionRun(Base):
    """
    Stores one execution of the DataGuard Inspector Agent
    against a dataset.
    """

    dataset_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    highest_severity: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    column_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    finding_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    audit_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    audit_hmac: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    findings = relationship(
        "InspectionFinding",
        back_populates="inspection_run",
        cascade="all, delete-orphan",
    )

    ml_proofs = relationship(
        "MLDetectionProof",
        back_populates="inspection_run",
        cascade="all, delete-orphan",
    )