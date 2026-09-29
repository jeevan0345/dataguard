from dataclasses import dataclass
from typing import Optional


@dataclass
class Finding:
    """
    Structured finding generated from an ETL anomaly.
    """

    metric: str
    finding_type: str
    severity: str

    actual_value: float
    expected_average: float

    lower_bound: float
    upper_bound: float

    deviation: float

    evidence: str
    likely_area: str
    explanation: str


def determine_severity(
    metric: str,
    deviation: float,
) -> str:
    """
    Determine severity based on the magnitude of deviation.
    """

    deviation_percent = deviation * 100

    # Output volume and output ratio are especially
    # important because large reductions can indicate
    # significant data loss.
    if metric in {
        "Output Rows",
        "Output/Input Ratio",
    }:
        if deviation_percent >= 50:
            return "CRITICAL"

        if deviation_percent >= 20:
            return "HIGH"

        if deviation_percent >= 5:
            return "MEDIUM"

        return "LOW"

    # Other metrics use a slightly more conservative scale.
    if deviation_percent >= 50:
        return "HIGH"

    if deviation_percent >= 20:
        return "MEDIUM"

    if deviation_percent >= 5:
        return "LOW"

    return "INFO"


def determine_finding_type(
    metric: str,
) -> str:
    """
    Convert a metric anomaly into a meaningful finding type.
    """

    mapping = {
        "Input Rows": "Input Volume Anomaly",
        "Output Rows": "Output Volume Anomaly",
        "Execution Duration (ms)": "Execution Performance Anomaly",
        "Output/Input Ratio": "Output Conversion Ratio Anomaly",
    }

    return mapping.get(
        metric,
        "ETL Metric Anomaly",
    )


def determine_likely_area(
    metric: str,
) -> str:
    """
    Provide a broad likely ETL area associated with
    the detected anomaly.
    """

    mapping = {
        "Input Rows": (
            "Source ingestion or upstream data availability"
        ),
        "Output Rows": (
            "Transformation, filtering, aggregation, "
            "or loading stage"
        ),
        "Execution Duration (ms)": (
            "Transformation, database query, "
            "resource utilization, or loading stage"
        ),
        "Output/Input Ratio": (
            "Transformation, filtering, validation, "
            "or loading stage"
        ),
    }

    return mapping.get(
        metric,
        "ETL pipeline",
    )


def generate_evidence(
    metric: str,
    actual: float,
    expected_average: float,
    lower_bound: float,
    upper_bound: float,
    deviation: float,
) -> str:
    """
    Generate human-readable evidence for an anomaly.
    """

    deviation_percent = deviation * 100

    return (
        f"Actual value: {actual:.2f}. "
        f"Historical average: {expected_average:.2f}. "
        f"Expected range: "
        f"{lower_bound:.2f} to {upper_bound:.2f}. "
        f"Deviation from historical average: "
        f"{deviation_percent:.2f}%."
    )


def create_finding(
    metric: str,
    actual: float,
    expected_average: float,
    lower_bound: float,
    upper_bound: float,
    deviation: float,
) -> Optional[Finding]:
    """
    Create a structured finding for an anomalous metric.

    Non-anomalous metrics are ignored.
    """

    if deviation < 0.05:
        return None

    finding_type = determine_finding_type(
        metric
    )

    severity = determine_severity(
        metric,
        deviation,
    )

    likely_area = determine_likely_area(
        metric
    )

    evidence = generate_evidence(
        metric=metric,
        actual=actual,
        expected_average=expected_average,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        deviation=deviation,
    )

    explanation = (
        f"{finding_type} detected. "
        f"The {metric} metric deviates significantly "
        f"from historical behaviour."
    )

    return Finding(
        metric=metric,
        finding_type=finding_type,
        severity=severity,
        actual_value=actual,
        expected_average=expected_average,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        deviation=deviation,
        evidence=evidence,
        likely_area=likely_area,
        explanation=explanation,
    )


def generate_findings(
    anomaly_result,
) -> list[Finding]:
    """
    Convert anomaly detector results into structured findings.
    """

    findings: list[Finding] = []

    for metric in anomaly_result.metrics:

        if not metric.is_anomaly:
            continue

        finding = create_finding(
            metric=metric.metric,
            actual=metric.actual,
            expected_average=metric.average,
            lower_bound=metric.lower_bound,
            upper_bound=metric.upper_bound,
            deviation=metric.deviation,
        )

        if finding is not None:
            findings.append(finding)

    return findings