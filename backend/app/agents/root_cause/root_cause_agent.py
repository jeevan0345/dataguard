"""
DataGuard Root Cause Agent
Performs cross-finding evidence correlation and diagnostic hypothesis ranking.
"""

from typing import Any
from app.agents.base.base_agent import BaseAgent
from app.audit.root_cause import (
    RootCauseCandidate,
    RootCauseResult,
    analyze_inspection_evidence,
)


class RootCauseAgent(BaseAgent):
    """
    Root Cause Agent for DataGuard 2.0.
    Evolves deterministic RCA into cross-finding synthesis:
    correlates schema drift, quality anomalies, and ML signals
    into ranked root causes with confidence scores.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Root Cause Agent",
            role="Diagnostic Reasoning & Evidence Correlation",
            description="Correlates multi-source audit evidence to infer root causes and affected pipeline stages.",
        )

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.diagnose(*args, **kwargs)

    def diagnose(
        self,
        evidence_data: dict[str, Any],
        pipeline_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Synthesizes individual evidence items and detects cross-finding patterns.
        """
        # 1. Base deterministic evaluation
        base_rca = analyze_inspection_evidence(evidence_data)

        # 2. Extract evidence items
        evidence_items = evidence_data.get("evidence", [])
        finding_types = [item.get("finding_type", "") for item in evidence_items]

        # 3. Cross-Finding Correlation Engine
        synthesized_candidates: list[dict[str, Any]] = []

        for candidate in base_rca.candidates:
            synthesized_candidates.append({
                "cause": candidate.cause,
                "confidence": candidate.confidence,
                "evidence": candidate.evidence,
                "affected_area": candidate.affected_area,
                "explanation": candidate.explanation,
                "level": "INDIVIDUAL",
            })

        # Pattern 1: Schema Change + Data Quality Failure = Upstream Breaking Contract
        has_schema_break = any(t in ["COLUMN_REMOVED", "COLUMN_TYPE_CHANGED"] for t in finding_types)
        has_quality_break = any(t in ["MISSING_VALUES", "DUPLICATE_RECORDS"] for t in finding_types)
        if has_schema_break and has_quality_break:
            synthesized_candidates.insert(0, {
                "cause": "Upstream Breaking Schema & Extraction Contract Change",
                "confidence": 0.95,
                "evidence": [
                    "Simultaneous occurrence of schema drift and data quality failure.",
                    f"Observed finding types: {', '.join(set(finding_types))}",
                ],
                "affected_area": "Upstream Source Database / API Contract",
                "explanation": (
                    "The simultaneous presence of missing/type-altered columns alongside null or malformed data "
                    "strongly indicates the source producer altered its data contract without backwards compatibility."
                ),
                "level": "CROSS_FINDING_SYNTHESIS",
            })

        # Pattern 2: Duplicates + Volume Increase = Replay or Non-Idempotent Ingestion
        if "DUPLICATE_RECORDS" in finding_types:
            for item in evidence_items:
                if item.get("finding_type") == "DUPLICATE_RECORDS":
                    ev = item.get("evidence", {})
                    pct = ev.get("duplicate_percentage", 0)
                    if pct > 10.0:
                        synthesized_candidates.insert(0, {
                            "cause": "Non-Idempotent Pipeline Extraction or Message Replay",
                            "confidence": 0.92,
                            "evidence": [
                                f"High duplicate rate of {pct:.1f}%.",
                                "Target table lacks unique composite key constraints.",
                            ],
                            "affected_area": "ETL Ingestion & Message Broker Queue",
                            "explanation": (
                                f"With {pct:.1f}% duplicate rows, pipeline execution was likely retried "
                                "without an idempotent upsert key or deduplication window."
                            ),
                            "level": "CROSS_FINDING_SYNTHESIS",
                        })
                        break

        # Pattern 3: ML Multivariate Anomalies + Outlier Spikes
        has_ml_anom = "ML_ISOLATION_FOREST_ANOMALY" in finding_types
        has_outliers = "NUMERICAL_OUTLIERS" in finding_types
        if has_ml_anom or has_outliers:
            synthesized_candidates.insert(0, {
                "cause": "Upstream Numerical Calculation or Sensor Data Drift",
                "confidence": 0.88,
                "evidence": [
                    "Unsupervised Isolation Forest flagged multivariate outliers.",
                    "Univariate numerical distribution bounds violated.",
                ],
                "affected_area": "ETL Transformation & Domain Feature Engineering",
                "explanation": (
                    "Records display multidimensional anomalies not accounted for by individual boundary checks. "
                    "Suggests bad currency conversion, sensor calibration offset, or transformation formula error."
                ),
                "level": "CROSS_FINDING_SYNTHESIS",
            })

        # Pattern 4: Distribution Drift (Concept / Seasonality Drift)
        if "DISTRIBUTION_DRIFT" in finding_types:
            synthesized_candidates.insert(0, {
                "cause": "Statistical Distribution Shift / Concept Drift",
                "confidence": 0.86,
                "evidence": [
                    "Two-sample Kolmogorov-Smirnov test rejected null hypothesis of identical distributions.",
                ],
                "affected_area": "Source Environment / Seasonal Consumer Behavior",
                "explanation": (
                    "Current dataset distributions have significantly diverged from historical baseline distributions. "
                    "Thresholds, transformations, or ML models consuming this pipeline require recalibration."
                ),
                "level": "CROSS_FINDING_SYNTHESIS",
            })

        # Sort candidates by confidence
        synthesized_candidates.sort(key=lambda c: c["confidence"], reverse=True)
        primary_cause = synthesized_candidates[0]["cause"] if synthesized_candidates else "Unknown"
        top_confidence = synthesized_candidates[0]["confidence"] if synthesized_candidates else 0.0

        return {
            "agent": self.name,
            "status": "DIAGNOSIS_COMPLETE",
            "finding_count": len(evidence_items),
            "primary_cause": primary_cause,
            "overall_confidence": top_confidence,
            "candidates": synthesized_candidates,
            "summary": (
                f"DataGuard Root Cause Agent correlated {len(evidence_items)} evidence item(s) "
                f"and identified '{primary_cause}' as the most probable root cause "
                f"(confidence: {top_confidence * 100:.1f}%)."
            ),
        }
