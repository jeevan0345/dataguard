from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.models import ETLRun


@dataclass
class MetricBaseline:
    """
    Historical baseline for one ETL metric.
    """

    average: float
    std_deviation: float
    lower_bound: float
    upper_bound: float


@dataclass
class ETLBaseline:
    """
    Complete historical baseline for a pipeline and dataset.
    """

    pipeline_id: str
    dataset_id: Optional[str]

    successful_runs: int

    input_rows: Optional[MetricBaseline]
    output_rows: Optional[MetricBaseline]
    duration_ms: Optional[MetricBaseline]
    output_ratio: Optional[MetricBaseline]


def create_metric_baseline(
    values: list[float],
) -> Optional[MetricBaseline]:
    """
    Calculate the historical average and normal range
    for one ETL metric.
    """

    if not values:
        return None

    average = mean(values)

    if len(values) > 1:
        std_deviation = pstdev(values)
    else:
        std_deviation = 0.0

    lower_bound = max(
        0.0,
        average - (2 * std_deviation),
    )

    upper_bound = (
        average + (2 * std_deviation)
    )

    return MetricBaseline(
        average=average,
        std_deviation=std_deviation,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )


def build_baseline(
    db: Session,
    pipeline_id: str,
    dataset_id: Optional[str] = None,
    min_runs: int = 3,
    exclude_run_id: Optional[UUID] = None,
) -> ETLBaseline:
    """
    Build a historical baseline using successful ETL runs.

    The current run is excluded from the baseline so that
    an anomalous run cannot influence its own expected range.
    """

    query = (
        db.query(ETLRun)
        .filter(
            ETLRun.pipeline_id == pipeline_id,
            ETLRun.status == "SUCCESS",
            ETLRun.is_active.is_(True),
        )
    )

    if dataset_id is not None:
        query = query.filter(
            ETLRun.dataset_id == dataset_id
        )

    # Exclude the run currently being analyzed.
    if exclude_run_id is not None:
        query = query.filter(
            ETLRun.id != exclude_run_id
        )

    runs = (
        query
        .order_by(ETLRun.started_at.desc())
        .all()
    )

    if len(runs) < min_runs:
        raise ValueError(
            f"At least {min_runs} historical successful "
            f"runs are required to build a baseline. "
            f"Found {len(runs)}."
        )

    input_rows = [
        float(run.rows_input)
        for run in runs
        if run.rows_input is not None
    ]

    output_rows = [
        float(run.rows_output)
        for run in runs
        if run.rows_output is not None
    ]

    duration_ms = [
        float(run.duration_ms)
        for run in runs
        if run.duration_ms is not None
    ]

    output_ratios = []

    for run in runs:
        if (
            run.rows_input is not None
            and run.rows_output is not None
            and run.rows_input > 0
        ):
            output_ratios.append(
                run.rows_output / run.rows_input
            )

    return ETLBaseline(
        pipeline_id=pipeline_id,
        dataset_id=dataset_id,
        successful_runs=len(runs),
        input_rows=create_metric_baseline(
            input_rows
        ),
        output_rows=create_metric_baseline(
            output_rows
        ),
        duration_ms=create_metric_baseline(
            duration_ms
        ),
        output_ratio=create_metric_baseline(
            output_ratios
        ),
    )