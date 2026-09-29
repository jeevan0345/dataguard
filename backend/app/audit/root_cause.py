from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.models import ETLFinding


@dataclass
class RootCauseCandidate:
    """
    Represents a possible root cause identified from
    ETL finding evidence.
    """

    cause: str
    confidence: float
    evidence: list[str]
    affected_area: str
    explanation: str


@dataclass
class RootCauseResult:
    """
    Complete root-cause analysis for an ETL run.
    """

    run_id: str
    finding_count: int
    primary_cause: Optional[str]
    overall_confidence: float
    candidates: list[RootCauseCandidate]
    summary: str


def analyze_output_volume_finding(
    finding: ETLFinding,
) -> RootCauseCandidate:
    """
    Analyze a significant reduction in ETL output volume.
    """

    evidence = [
        (
            f"Output rows were {finding.actual_value:.0f}, "
            f"compared with a historical expected average "
            f"of approximately "
            f"{finding.expected_average:.0f} rows."
        ),
        (
            f"The expected output range was "
            f"{finding.lower_bound:.0f} to "
            f"{finding.upper_bound:.0f} rows."
        ),
        (
            f"Observed output deviation was "
            f"{finding.deviation * 100:.2f}%."
        ),
    ]

    return RootCauseCandidate(
        cause=(
            "Potential record loss during "
            "ETL transformation, filtering, aggregation, "
            "or loading."
        ),
        confidence=0.85,
        evidence=evidence,
        affected_area=(
            "Transformation, filtering, aggregation, "
            "or loading"
        ),
        explanation=(
            "The output volume is substantially lower "
            "than historical behaviour. This suggests "
            "that records may have been removed or "
            "discarded during an ETL processing stage."
        ),
    )


def analyze_output_ratio_finding(
    finding: ETLFinding,
) -> RootCauseCandidate:
    """
    Analyze an abnormal output/input ratio.
    """

    evidence = [
        (
            f"Observed output/input ratio was "
            f"{finding.actual_value:.4f}."
        ),
        (
            f"Historical expected ratio was "
            f"{finding.expected_average:.4f}."
        ),
        (
            f"The expected ratio range was "
            f"{finding.lower_bound:.4f} to "
            f"{finding.upper_bound:.4f}."
        ),
        (
            f"Ratio deviation was "
            f"{finding.deviation * 100:.2f}%."
        ),
    ]

    return RootCauseCandidate(
        cause=(
            "Unexpected filtering, validation rejection, "
            "transformation loss, or incomplete loading."
        ),
        confidence=0.90,
        evidence=evidence,
        affected_area=(
            "Transformation, filtering, validation, "
            "or loading"
        ),
        explanation=(
            "The proportion of records successfully "
            "produced by the pipeline is substantially "
            "below historical behaviour. This indicates "
            "that records may have been rejected, "
            "filtered, transformed incorrectly, or "
            "not loaded successfully."
        ),
    )


def analyze_generic_finding(
    finding: ETLFinding,
) -> RootCauseCandidate:
    """
    Fallback analysis for finding types that do not yet
    have specialized RCA rules.
    """

    evidence = [
        finding.evidence,
    ]

    return RootCauseCandidate(
        cause=(
            f"Abnormal behaviour associated with "
            f"{finding.metric}."
        ),
        confidence=0.50,
        evidence=evidence,
        affected_area=finding.likely_area,
        explanation=(
            "The metric differs significantly from "
            "historical behaviour. Additional pipeline "
            "logs and execution evidence are required "
            "to confirm the root cause."
        ),
    )


def analyze_finding(
    finding: ETLFinding,
) -> RootCauseCandidate:
    """
    Select the appropriate RCA analysis for a finding.
    """

    if finding.metric == "Output Rows":
        return analyze_output_volume_finding(
            finding
        )

    if finding.metric == "Output/Input Ratio":
        return analyze_output_ratio_finding(
            finding
        )

    return analyze_generic_finding(
        finding
    )


def merge_candidates(
    candidates: list[RootCauseCandidate],
) -> list[RootCauseCandidate]:
    """
    Merge closely related record-loss candidates.
    """

    if not candidates:
        return []

    record_loss_candidates = [
        candidate
        for candidate in candidates
        if (
            "record loss" in candidate.cause.lower()
            or "filtering" in candidate.cause.lower()
            or "loading" in candidate.cause.lower()
        )
    ]

    other_candidates = [
        candidate
        for candidate in candidates
        if candidate not in record_loss_candidates
    ]

    if record_loss_candidates:
        combined_evidence: list[str] = []

        for candidate in record_loss_candidates:
            combined_evidence.extend(
                candidate.evidence
            )

        highest_confidence = max(
            candidate.confidence
            for candidate in record_loss_candidates
        )

        combined = RootCauseCandidate(
            cause=(
                "Potential record loss during ETL "
                "transformation, filtering, validation, "
                "or loading."
            ),
            confidence=highest_confidence,
            evidence=combined_evidence,
            affected_area=(
                "Transformation, filtering, validation, "
                "or loading"
            ),
            explanation=(
                "Multiple independent findings indicate "
                "a substantial reduction in records "
                "through the ETL pipeline. The evidence "
                "supports investigating transformation, "
                "filtering, validation, and loading stages."
            ),
        )

        return [combined] + other_candidates

    return candidates


def analyze_run_root_cause(
    db: Session,
    run_id: UUID,
) -> RootCauseResult:
    """
    Perform deterministic root-cause analysis using
    persisted ETL findings.
    """

    findings = (
        db.query(ETLFinding)
        .filter(
            ETLFinding.run_id == run_id,
            ETLFinding.is_active.is_(True),
        )
        .order_by(
            ETLFinding.created_at.asc()
        )
        .all()
    )

    if not findings:
        raise ValueError(
            "No persisted findings were found for this ETL run."
        )

    candidates = [
        analyze_finding(finding)
        for finding in findings
    ]

    candidates = merge_candidates(
        candidates
    )

    if not candidates:
        return RootCauseResult(
            run_id=str(run_id),
            finding_count=len(findings),
            primary_cause=None,
            overall_confidence=0.0,
            candidates=[],
            summary=(
                "No root-cause candidates could be "
                "identified from the available findings."
            ),
        )

    primary_candidate = max(
        candidates,
        key=lambda candidate: candidate.confidence,
    )

    overall_confidence = (
        primary_candidate.confidence
    )

    summary = (
        "Root-cause analysis indicates that "
        "record loss or unexpected filtering may "
        "have occurred during the ETL process. "
        "This is a candidate root cause and requires "
        "additional pipeline evidence for confirmation."
    )

    return RootCauseResult(
        run_id=str(run_id),
        finding_count=len(findings),
        primary_cause=primary_candidate.cause,
        overall_confidence=overall_confidence,
        candidates=candidates,
        summary=summary,
    )
def analyze_inspection_evidence(
    evidence_result: dict,
) -> RootCauseResult:
    """
    Perform root-cause analysis using structured evidence
    produced by the Evidence Engine.

    This analysis is deterministic and evidence-based.
    It identifies likely causes rather than claiming
    a confirmed root cause.
    """

    evidence_items = evidence_result.get(
        "evidence",
        [],
    )

    if not evidence_items:
        return RootCauseResult(
            run_id="inspection",
            finding_count=0,
            primary_cause=None,
            overall_confidence=0.0,
            candidates=[],
            summary=(
                "No evidence was available for "
                "root-cause analysis."
            ),
        )

    candidates: list[RootCauseCandidate] = []

    for item in evidence_items:

        finding_type = item.get(
            "finding_type",
            "UNKNOWN",
        )

        severity = item.get(
            "severity",
            "UNKNOWN",
        )

        message = item.get(
            "message",
            "",
        )

        evidence = item.get(
            "evidence",
            {},
        )

        if finding_type == "MISSING_VALUES":

            column = evidence.get(
                "column",
                "unknown",
            )

            missing_percentage = evidence.get(
                "missing_percentage",
                0,
            )

            candidates.append(
                RootCauseCandidate(
                    cause=(
                        "Potential incomplete source data "
                        "or missing records during data ingestion."
                    ),
                    confidence=0.75,
                    evidence=[
                        (
                            f"Column '{column}' contains "
                            f"{missing_percentage}% missing values."
                        ),
                        (
                            f"Finding severity was "
                            f"{severity}."
                        ),
                    ],
                    affected_area=(
                        "Source data or data ingestion"
                    ),
                    explanation=(
                        "A significant number of missing "
                        "values were detected in the dataset. "
                        "This may indicate incomplete source "
                        "data or an issue during ingestion."
                    ),
                )
            )

        elif finding_type == "DUPLICATE_RECORDS":

            duplicate_percentage = evidence.get(
                "duplicate_percentage",
                0,
            )

            candidates.append(
                RootCauseCandidate(
                    cause=(
                        "Potential duplicate data introduced "
                        "during extraction, transformation, "
                        "or loading."
                    ),
                    confidence=0.80,
                    evidence=[
                        (
                            f"Duplicate records represent "
                            f"{duplicate_percentage}% of the dataset."
                        ),
                        (
                            f"Finding severity was "
                            f"{severity}."
                        ),
                    ],
                    affected_area=(
                        "Extraction, transformation, "
                        "or loading"
                    ),
                    explanation=(
                        "Duplicate records were detected. "
                        "This may indicate repeated extraction, "
                        "missing deduplication, or duplicate "
                        "loading into the target dataset."
                    ),
                )
            )

        elif finding_type == "COLUMN_REMOVED":

            column = evidence.get(
                "column",
                "unknown",
            )

            expected_type = evidence.get(
                "expected_type",
                "unknown",
            )

            candidates.append(
                RootCauseCandidate(
                    cause=(
                        "Potential upstream schema change "
                        "or ETL transformation removing "
                        "an expected column."
                    ),
                    confidence=0.90,
                    evidence=[
                        (
                            f"Expected column '{column}' "
                            f"was not found."
                        ),
                        (
                            f"Expected data type was "
                            f"'{expected_type}'."
                        ),
                    ],
                    affected_area=(
                        "Source schema or transformation"
                    ),
                    explanation=(
                        "A column defined in the expected "
                        "schema is missing from the actual "
                        "dataset. This suggests a possible "
                        "upstream schema change or a "
                        "transformation that removed the column."
                    ),
                )
            )

        elif finding_type == "COLUMN_ADDED":

            column = evidence.get(
                "column",
                "unknown",
            )

            actual_type = evidence.get(
                "actual_type",
                "unknown",
            )

            candidates.append(
                RootCauseCandidate(
                    cause=(
                        "Potential upstream schema expansion "
                        "or source-system change."
                    ),
                    confidence=0.70,
                    evidence=[
                        (
                            f"Unexpected column '{column}' "
                            f"was detected."
                        ),
                        (
                            f"Actual data type was "
                            f"'{actual_type}'."
                        ),
                    ],
                    affected_area=(
                        "Source schema"
                    ),
                    explanation=(
                        "A new column was detected that was "
                        "not present in the expected schema. "
                        "This may indicate an upstream source "
                        "system change."
                    ),
                )
            )

        elif finding_type == "COLUMN_TYPE_CHANGED":

            column = evidence.get(
                "column",
                "unknown",
            )

            expected_type = evidence.get(
                "expected_type",
                "unknown",
            )

            actual_type = evidence.get(
                "actual_type",
                "unknown",
            )

            candidates.append(
                RootCauseCandidate(
                    cause=(
                        "Potential upstream schema type change "
                        "or transformation type conversion."
                    ),
                    confidence=0.85,
                    evidence=[
                        (
                            f"Column '{column}' changed "
                            f"from '{expected_type}' "
                            f"to '{actual_type}'."
                        ),
                    ],
                    affected_area=(
                        "Source schema or transformation"
                    ),
                    explanation=(
                        "The detected data type differs from "
                        "the expected type. This may indicate "
                        "an upstream schema change or an "
                        "unexpected transformation."
                    ),
                )
            )

        else:

            candidates.append(
                RootCauseCandidate(
                    cause=(
                        f"Potential issue associated with "
                        f"{finding_type}."
                    ),
                    confidence=0.50,
                    evidence=[
                        message,
                    ],
                    affected_area=(
                        "ETL pipeline"
                    ),
                    explanation=(
                        "The finding indicates abnormal "
                        "behaviour, but additional pipeline "
                        "evidence is required to determine "
                        "the root cause."
                    ),
                )
            )

    primary_candidate = max(
        candidates,
        key=lambda candidate: candidate.confidence,
    )

    return RootCauseResult(
        run_id="inspection",
        finding_count=len(evidence_items),
        primary_cause=primary_candidate.cause,
        overall_confidence=primary_candidate.confidence,
        candidates=candidates,
        summary=(
            "Root-cause analysis identified candidate "
            "causes based on the available inspection "
            "evidence. These causes are not confirmed and "
            "require additional pipeline evidence for "
            "verification."
        ),
    )