from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.models import ETLRun


class ETLAuditService:
    """
    Business logic for creating, updating and retrieving ETL runs.
    """

    @staticmethod
    def create_run(
        db: Session,
        pipeline_id: str,
        dataset_id: Optional[str],
        started_at: datetime,
        status: str = "RUNNING",
        rows_input: Optional[int] = None,
        rows_output: Optional[int] = None,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        checkpoint: Optional[str] = None,
    ) -> ETLRun:

        run = ETLRun(
            pipeline_id=pipeline_id,
            dataset_id=dataset_id,
            started_at=started_at,
            status=status,
            rows_input=rows_input,
            rows_output=rows_output,
            duration_ms=duration_ms,
            error_message=error_message,
            checkpoint=checkpoint,
        )

        db.add(run)
        db.commit()
        db.refresh(run)

        return run

    @staticmethod
    def update_run(
        db: Session,
        run_id: UUID,
        completed_at: Optional[datetime] = None,
        status: Optional[str] = None,
        rows_input: Optional[int] = None,
        rows_output: Optional[int] = None,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        checkpoint: Optional[str] = None,
    ) -> Optional[ETLRun]:

        run = (
            db.query(ETLRun)
            .filter(
                ETLRun.id == run_id,
                ETLRun.is_active.is_(True),
            )
            .first()
        )

        if run is None:
            return None

        if completed_at is not None:
            run.completed_at = completed_at

        if status is not None:
            run.status = status

        if rows_input is not None:
            run.rows_input = rows_input

        if rows_output is not None:
            run.rows_output = rows_output

        if duration_ms is not None:
            run.duration_ms = duration_ms

        if error_message is not None:
            run.error_message = error_message

        if checkpoint is not None:
            run.checkpoint = checkpoint

        # If the run has completed but duration wasn't supplied,
        # calculate it automatically.
        if (
            run.completed_at is not None
            and run.started_at is not None
            and run.duration_ms is None
        ):
            duration = (
                run.completed_at - run.started_at
            ).total_seconds() * 1000

            run.duration_ms = duration

        db.commit()
        db.refresh(run)

        return run

    @staticmethod
    def get_run(
        db: Session,
        run_id: UUID,
    ) -> Optional[ETLRun]:

        return (
            db.query(ETLRun)
            .filter(
                ETLRun.id == run_id,
                ETLRun.is_active.is_(True),
            )
            .first()
        )

    @staticmethod
    def get_runs(
        db: Session,
        pipeline_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[ETLRun]:

        query = (
            db.query(ETLRun)
            .filter(ETLRun.is_active.is_(True))
        )

        if pipeline_id is not None:
            query = query.filter(
                ETLRun.pipeline_id == pipeline_id
            )

        if dataset_id is not None:
            query = query.filter(
                ETLRun.dataset_id == dataset_id
            )

        if status is not None:
            query = query.filter(
                ETLRun.status == status
            )

        return (
            query
            .order_by(ETLRun.started_at.desc())
            .limit(limit)
            .all()
        )