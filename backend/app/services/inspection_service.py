from typing import Any

from sqlalchemy.orm import Session

from app.agents.inspector.inspector_agent import InspectorAgent
from app.audit.root_cause import analyze_inspection_evidence
from app.evidence.evidence_builder import EvidenceBuilder
from app.etl.extractor.dataset_loader import DatasetLoader
from app.etl.extractor.schema_inference import SchemaInference
from app.services.inspection_finding_service import (
    InspectionFindingService,
)


class InspectionService:
    """
    Orchestrates the complete DataGuard inspection workflow.

    Workflow:

        Dataset
           ↓
        Dataset Loader
           ↓
        Schema Inference
           ↓
        Inspector Agent
           ↓
        Evidence Engine
           ↓
        Root Cause Analysis
           ↓
        PostgreSQL Persistence
           ↓
        API Response
    """

    def __init__(self) -> None:
        self.inspector_agent = InspectorAgent()
        self.evidence_builder = EvidenceBuilder()

    def inspect_dataset(
        self,
        dataset_path: str,
        expected_schema: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Load a dataset from disk and perform a complete
        inspection without database persistence.
        """

        # -----------------------------------------------------
        # 1. Load dataset
        # -----------------------------------------------------
        rows = DatasetLoader.load_dataset(
            dataset_path
        )

        # -----------------------------------------------------
        # 2. Inspect loaded rows
        # -----------------------------------------------------
        return self.inspect_rows(
            rows=rows,
            expected_schema=expected_schema,
            dataset_path=dataset_path,
        )

    def inspect_dataset_and_persist(
        self,
        db: Session,
        dataset_path: str,
        expected_schema: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Load a dataset, perform inspection, generate evidence,
        perform root-cause analysis, and persist the inspection.
        """

        # -----------------------------------------------------
        # 1. Load dataset
        # -----------------------------------------------------
        rows = DatasetLoader.load_dataset(
            dataset_path
        )

        from app.services.baseline_service import BaselineService
        baseline = BaselineService.get_baseline(db, dataset_path)
        reference_rows = baseline.reference_sample if baseline else None

        # -----------------------------------------------------
        # 2. Perform complete inspection
        # -----------------------------------------------------
        result = self.inspect_rows(
            rows=rows,
            expected_schema=expected_schema,
            dataset_path=dataset_path,
            reference_rows=reference_rows,
        )

        # -----------------------------------------------------
        # 3. Persist inspection findings
        # -----------------------------------------------------
        inspection_result = result["inspection"]

        inspection_run = (
            InspectionFindingService.save_inspection(
                db=db,
                dataset_path=dataset_path,
                inspection_result=inspection_result,
                row_count=result["row_count"],
                column_count=result["column_count"],
            )
        )

        # -----------------------------------------------------
        # 4. Add persistence information
        # -----------------------------------------------------
        result["inspection_id"] = str(
            inspection_run.id
        )

        result["persistence"] = {
            "saved": True,
            "inspection_id": str(
                inspection_run.id
            ),
            "finding_count": (
                inspection_run.finding_count
            ),
        }

        return result

    def inspect_rows(
        self,
        rows: list[dict[str, Any]],
        expected_schema: dict[str, str] | None = None,
        dataset_path: str | None = None,
        reference_rows: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Perform the complete DataGuard inspection workflow
        on rows already available in memory.

        This includes:

        1. Input validation
        2. Schema inference
        3. Inspector Agent
        4. Evidence Engine
        5. Root Cause Analysis
        """

        # -----------------------------------------------------
        # 1. Validate input
        # -----------------------------------------------------
        if not isinstance(rows, list):
            raise TypeError(
                "rows must be a list of dictionaries."
            )

        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise TypeError(
                    f"Row at index {index} must be a dictionary."
                )

        # -----------------------------------------------------
        # 2. Infer actual schema
        # -----------------------------------------------------
        actual_schema = (
            SchemaInference.infer_schema(rows)
        )

        # -----------------------------------------------------
        # 3. Run Inspector Agent
        # -----------------------------------------------------
        inspection_result = (
            self.inspector_agent.inspect(
                rows=rows,
                expected_schema=expected_schema,
                actual_schema=actual_schema,
                reference_rows=reference_rows,
            )
        )

        # -----------------------------------------------------
        # 4. Build structured evidence
        # -----------------------------------------------------
        evidence_result = (
            self.evidence_builder.build(
                inspection_result
            )
        )

        # -----------------------------------------------------
        # 5. Perform root-cause analysis
        # -----------------------------------------------------
        root_cause_result = (
            analyze_inspection_evidence(
                evidence_result
            )
        )

        # -----------------------------------------------------
        # 6. Convert RCA dataclasses to dictionaries
        # -----------------------------------------------------
        root_cause = {
            "run_id": root_cause_result.run_id,
            "finding_count": (
                root_cause_result.finding_count
            ),
            "primary_cause": (
                root_cause_result.primary_cause
            ),
            "overall_confidence": (
                root_cause_result.overall_confidence
            ),
            "summary": root_cause_result.summary,
            "candidates": [
                {
                    "cause": candidate.cause,
                    "confidence": candidate.confidence,
                    "evidence": candidate.evidence,
                    "affected_area": candidate.affected_area,
                    "explanation": candidate.explanation,
                }
                for candidate
                in root_cause_result.candidates
            ],
        }

        # -----------------------------------------------------
        # 7. Return complete inspection result
        # -----------------------------------------------------
        return {
            "dataset_path": dataset_path,
            "row_count": len(rows),
            "column_count": len(actual_schema),
            "actual_schema": actual_schema,
            "inspection": inspection_result,
            "evidence": evidence_result,
            "root_cause": root_cause,
        }