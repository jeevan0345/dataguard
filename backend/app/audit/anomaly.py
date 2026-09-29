from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.baseline import (
    ETLBaseline,
    MetricBaseline,
    build_baseline,
)
from app.audit.models import ETLRun


# Minimum relative deviation required before
# a metric can be considered anomalous.
MIN_DEVIATION_THRESHOLD = 0.05


@dataclass
class MetricAnomaly:
    """
    Result of comparing one ETL metric with its
    historical baseline.
    """

    metric: str
    actual: float
    average: float
    lower_bound: float
    upper_bound: float
    deviation: float
    is_anomaly: bool
    explanation: str


@dataclass
class AnomalyResult:
    """
    Complete anomaly analysis for one ETL run.
    """

    run_id: str
    pipeline_id: str
    dataset_id: Optional[str]

    is_anomaly: bool
    anomaly_score: float

    metrics: list[MetricAnomaly]

    summary: str


def check_metric(
    metric_name: str,
    actual: Optional[float],
    baseline: Optional[MetricBaseline],
) -> Optional[MetricAnomaly]:
    """
    Compare one actual metric against its historical baseline.

    A metric must satisfy BOTH conditions to be classified
    as anomalous:

    1. It must be outside the historical normal range.
    2. Its relative deviation must be at least 5%.
    """

    if actual is None or baseline is None:
        return None

    if baseline.average == 0:
        deviation = 0.0
    else:
        deviation = (
            abs(actual - baseline.average)
            / abs(baseline.average)
        )

    outside_historical_range = (
        actual < baseline.lower_bound
        or actual > baseline.upper_bound
    )

    significant_deviation = (
        deviation >= MIN_DEVIATION_THRESHOLD
    )

    is_anomaly = (
        outside_historical_range
        and significant_deviation
    )

    if is_anomaly:
        explanation = (
            f"{metric_name} is significantly outside "
            f"the historical normal range. "
            f"Actual value is {actual:.2f}, while the "
            f"expected range is "
            f"{baseline.lower_bound:.2f} to "
            f"{baseline.upper_bound:.2f}. "
            f"The relative deviation is "
            f"{deviation * 100:.2f}%."
        )

    elif outside_historical_range:
        explanation = (
            f"{metric_name} is slightly outside the "
            f"historical range, but the deviation is only "
            f"{deviation * 100:.2f}%, which is below the "
            f"{MIN_DEVIATION_THRESHOLD * 100:.0f}% "
            f"anomaly threshold."
        )

    else:
        explanation = (
            f"{metric_name} is within the historical "
            f"normal range."
        )

    return MetricAnomaly(
        metric=metric_name,
        actual=actual,
        average=baseline.average,
        lower_bound=baseline.lower_bound,
        upper_bound=baseline.upper_bound,
        deviation=deviation,
        is_anomaly=is_anomaly,
        explanation=explanation,
    )


def analyze_run(
    db: Session,
    run_id: str,
    min_baseline_runs: int = 3,
) -> AnomalyResult:
    """
    Analyze one completed ETL run against its historical
    baseline.

    The current run is excluded from the baseline.
    """

    try:
        run_uuid = UUID(str(run_id))
    except ValueError:
        raise ValueError(
            "Invalid ETL run UUID."
        )

    run = (
        db.query(ETLRun)
        .filter(
            ETLRun.id == run_uuid,
            ETLRun.is_active.is_(True),
        )
        .first()
    )

    if run is None:
        raise ValueError(
            "ETL run not found."
        )

    if run.status != "SUCCESS":
        raise ValueError(
            "Only completed SUCCESS runs can be analyzed."
        )

    baseline: ETLBaseline = build_baseline(
        db=db,
        pipeline_id=run.pipeline_id,
        dataset_id=run.dataset_id,
        min_runs=min_baseline_runs,
        exclude_run_id=run.id,
    )

    metrics: list[MetricAnomaly] = []

    # -----------------------------------------------------
    # Input rows
    # -----------------------------------------------------

    input_result = check_metric(
        metric_name="Input Rows",
        actual=(
            float(run.rows_input)
            if run.rows_input is not None
            else None
        ),
        baseline=baseline.input_rows,
    )

    if input_result is not None:
        metrics.append(input_result)

    # -----------------------------------------------------
    # Output rows
    # -----------------------------------------------------

    output_result = check_metric(
        metric_name="Output Rows",
        actual=(
            float(run.rows_output)
            if run.rows_output is not None
            else None
        ),
        baseline=baseline.output_rows,
    )

    if output_result is not None:
        metrics.append(output_result)

    # -----------------------------------------------------
    # Execution duration
    # -----------------------------------------------------

    duration_result = check_metric(
        metric_name="Execution Duration (ms)",
        actual=(
            float(run.duration_ms)
            if run.duration_ms is not None
            else None
        ),
        baseline=baseline.duration_ms,
    )

    if duration_result is not None:
        metrics.append(duration_result)

    # -----------------------------------------------------
    # Output/Input ratio
    # -----------------------------------------------------

    output_ratio = None

    if (
        run.rows_input is not None
        and run.rows_output is not None
        and run.rows_input > 0
    ):
        output_ratio = (
            run.rows_output
            / run.rows_input
        )

    ratio_result = check_metric(
        metric_name="Output/Input Ratio",
        actual=output_ratio,
        baseline=baseline.output_ratio,
    )

    if ratio_result is not None:
        metrics.append(ratio_result)

    # -----------------------------------------------------
    # Overall anomaly score
    # -----------------------------------------------------

    anomaly_count = sum(
        1
        for metric in metrics
        if metric.is_anomaly
    )

    total_metrics = len(metrics)

    if total_metrics > 0:
        anomaly_score = (
            anomaly_count / total_metrics
        )
    else:
        anomaly_score = 0.0

    is_anomaly = anomaly_count > 0

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    if is_anomaly:

        anomalous_metrics = [
            metric.metric
            for metric in metrics
            if metric.is_anomaly
        ]

        summary = (
            "Anomaly detected in: "
            + ", ".join(anomalous_metrics)
        )

    else:

        summary = (
            "ETL run is within the historical "
            "baseline."
        )

    return AnomalyResult(
        run_id=str(run.id),
        pipeline_id=run.pipeline_id,
        dataset_id=run.dataset_id,
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
        metrics=metrics,
        summary=summary,
    )