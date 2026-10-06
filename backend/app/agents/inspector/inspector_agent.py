from typing import Any

from app.agents.base.base_agent import BaseAgent
from app.agents.inspector.data_quality import DataQualityAgent
from app.agents.inspector.schema_drift import SchemaDriftAgent
from app.ml.ml_engine import MLEngine


class InspectorAgent(BaseAgent):
    """
    Main Inspector Agent for DataGuard 2.0.

    The Inspector Agent coordinates:
    - Data Quality inspection (missing values, nulls, duplicates)
    - Schema Drift inspection (added/removed/type-changed columns)
    - ML Anomaly detection (Z-score, IQR fences, KS drift, Isolation Forest)

    It produces a unified inspection result that can later
    be consumed by the Root Cause, Recommendation, Recovery,
    Reporter and Copilot agents.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Inspector Agent",
            role="Data Quality, Schema Drift & ML Anomaly Inspection",
            description="Performs deep multimodal auditing across schema, data quality, and statistical/ML anomalies.",
        )
        self.agent_name = self.name

        self.data_quality_agent = DataQualityAgent()
        self.schema_drift_agent = SchemaDriftAgent()
        self.ml_engine = MLEngine()

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.inspect(*args, **kwargs)

    def inspect(
        self,
        rows: list[dict[str, Any]],
        expected_schema: dict[str, str] | None = None,
        actual_schema: dict[str, str] | None = None,
        reference_rows: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Run all available inspection checks.

        Parameters
        ----------
        rows:
            Dataset records to inspect.

        expected_schema:
            Previously expected schema for the dataset.

        actual_schema:
            Schema observed in the current dataset.

        Returns
        -------
        dict
            Unified Inspector Agent result.
        """

        # ---------------------------------------------------------
        # Data Quality Inspection
        # ---------------------------------------------------------
        data_quality_result = self.data_quality_agent.inspect(
            rows=rows
        )

        # ---------------------------------------------------------
        # Schema Drift Inspection
        # ---------------------------------------------------------
        schema_drift_result: dict[str, Any] | None = None

        if expected_schema is not None and actual_schema is not None:
            schema_drift_result = self.schema_drift_agent.inspect(
                expected_schema=expected_schema,
                actual_schema=actual_schema,
            )

        # ---------------------------------------------------------
        # ML Anomaly & Statistical Inspection
        # ---------------------------------------------------------
        ml_result = self.ml_engine.analyze(
            rows=rows,
            reference_rows=reference_rows,
        )

        # ---------------------------------------------------------
        # Collect all findings
        # ---------------------------------------------------------
        findings: list[dict[str, Any]] = []

        findings.extend(
            data_quality_result.get("findings", [])
        )

        if schema_drift_result is not None:
            findings.extend(
                schema_drift_result.get("findings", [])
            )

        findings.extend(
            ml_result.get("findings", [])
        )

        for f in findings:
            if not f.get("column") and f.get("evidence", {}).get("column"):
                f["column"] = f["evidence"]["column"]

        # ---------------------------------------------------------
        # Determine overall status
        # ---------------------------------------------------------
        if not findings:
            overall_status = "HEALTHY"
        else:
            overall_status = "ANOMALY_DETECTED"

        # ---------------------------------------------------------
        # Determine highest severity
        # ---------------------------------------------------------
        highest_severity = self._get_highest_severity(
            findings
        )

        # ---------------------------------------------------------
        # Final unified result
        # ---------------------------------------------------------
        return {
            "agent": self.agent_name,
            "status": overall_status,
            "highest_severity": highest_severity,
            "finding_count": len(findings),
            "findings": findings,
            "data_quality": data_quality_result,
            "schema_drift": schema_drift_result,
            "ml_analysis": ml_result,
            "ml_proof": ml_result.get("ml_proof", {}),
        }

    # -------------------------------------------------------------
    # Severity helper
    # -------------------------------------------------------------
    @staticmethod
    def _get_highest_severity(
        findings: list[dict[str, Any]],
    ) -> str | None:
        """
        Return the highest severity among all findings.
        """

        severity_order = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
        }

        highest: str | None = None
        highest_score = 0

        for finding in findings:
            severity = str(
                finding.get("severity", "")
            ).upper()

            score = severity_order.get(
                severity,
                0,
            )

            if score > highest_score:
                highest_score = score
                highest = severity

        return highest