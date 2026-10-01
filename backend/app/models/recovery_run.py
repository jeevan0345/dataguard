import json
import uuid
from typing import Any, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RecoveryRun(Base):
    """
    Stores an execution of the DataGuard Recovery Agent,
    persisting the actions applied, before/after metrics,
    and a reference to the remediated dataset artifact.
    """

    inspection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inspectionruns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    dataset_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RECOVERY_APPLIED",
        index=True,
    )

    verdict: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PASS",
        index=True,
    )

    original_row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    remediated_row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    actions_executed: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    remediated_file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    remediated_file_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    executed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    def get_actions(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.actions_executed)
        except Exception:
            return []
