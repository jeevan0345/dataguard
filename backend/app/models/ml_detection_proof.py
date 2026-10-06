import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MLDetectionProof(Base):
    """
    Stores auditable, method-by-method proof that anomaly/statistical
    detection algorithms executed on a dataset for an inspection run.

    Methods:
    - Z-SCORE (Inspector Agent)
    - IQR (Inspector Agent)
    - ISOLATION FOREST (Inspector Agent)
    - KS TWO-SAMPLE TEST (Drift Agent)
    """

    __tablename__ = "mldetectionproofs"

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspectionruns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dataset_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # "Z_SCORE", "IQR", "ISOLATION_FOREST", "KS_TEST"

    agent: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # "Inspector Agent", "Drift Agent"

    column_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        index=True,
    )

    execution_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="EXECUTED",
    )  # "EXECUTED", "NOT_EXECUTED", "FAILED", "NOT_APPLICABLE"

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # "ANOMALY_DETECTED", "OUTLIER_DETECTED", "DRIFT_DETECTED", "HEALTHY", "STABLE", "NOT_EXECUTED"

    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    baseline_sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    mean: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    std_dev: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    q3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iqr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lower_bound: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    ks_statistic: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    p_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    threshold: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    anomaly_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    prediction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    contamination: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    flagged_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    evidence: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="{}",
    )

    finding_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspectionfindings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    inspection_run = relationship("InspectionRun", back_populates="ml_proofs")
    finding = relationship("InspectionFinding")
