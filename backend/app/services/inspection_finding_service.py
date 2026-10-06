import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.inspection_finding import InspectionFinding
from app.models.inspection_run import InspectionRun
from app.evidence.evidence_builder import EvidenceBuilder


class InspectionFindingService:
    """
    Persists Inspector Agent results into PostgreSQL.

    One InspectionRun represents one execution of the
    Inspector Agent.

    Each finding generated during that inspection is stored
    as an InspectionFinding.
    """

    @staticmethod
    def save_inspection(
        db: Session,
        dataset_path: str,
        inspection_result: dict[str, Any],
        row_count: int,
        column_count: int,
    ) -> InspectionRun:
        """
        Save one complete inspection and all of its findings with cryptographic signatures.

        Existing findings are not reused. Each inspection execution
        creates a new InspectionRun, preserving the audit history.
        """
        status = inspection_result.get("status", "UNKNOWN")
        highest_severity = inspection_result.get("highest_severity")
        findings = inspection_result.get("findings", [])

        # Compute cryptographic tamper-evident signatures
        canonical = EvidenceBuilder.compute_canonical_audit(
            dataset_path=dataset_path,
            status=status,
            highest_severity=highest_severity,
            row_count=row_count,
            column_count=column_count,
            findings=findings,
        )
        audit_hash, audit_hmac = EvidenceBuilder.generate_audit_signatures(canonical)

        inspection_run = InspectionRun(
            dataset_path=dataset_path,
            status=status,
            highest_severity=highest_severity,
            row_count=row_count,
            column_count=column_count,
            finding_count=len(findings),
            summary=InspectionFindingService._build_summary(
                inspection_result,
            ),
            audit_hash=audit_hash,
            audit_hmac=audit_hmac,
        )

        db.add(inspection_run)
        db.flush()

        findings = inspection_result.get(
            "findings",
            [],
        )

        persisted_findings: list[InspectionFinding] = []
        for finding in findings:
            evidence = finding.get(
                "evidence",
                {},
            )

            inspection_finding = InspectionFinding(
                inspection_id=inspection_run.id,
                finding_type=finding.get(
                    "type",
                    "UNKNOWN",
                ),
                severity=finding.get(
                    "severity",
                    "UNKNOWN",
                ),
                message=finding.get(
                    "message",
                    "",
                ),
                evidence=json.dumps(
                    evidence,
                    default=str,
                ),
                column_name=evidence.get(
                    "column",
                ) or finding.get("column"),
                expected_type=evidence.get(
                    "expected_type",
                ),
                actual_type=evidence.get(
                    "actual_type",
                ),
            )

            db.add(inspection_finding)
            persisted_findings.append(inspection_finding)

        db.flush()

        # Persist transparent method-by-method ML detection proofs
        ml_proof_data = inspection_result.get("ml_proof") or inspection_result.get("ml_analysis", {}).get("ml_proof", {})
        if ml_proof_data:
            from app.services.ml_proof_service import MLProofService
            MLProofService.persist_ml_proofs(
                db=db,
                inspection_run=inspection_run,
                ml_proof_data=ml_proof_data,
                persisted_findings=persisted_findings,
            )

        db.commit()
        db.refresh(inspection_run)

        return inspection_run

    @staticmethod
    def get_inspection(
        db: Session,
        inspection_id,
    ) -> InspectionRun | None:
        """
        Retrieve one persisted inspection.
        """

        return (
            db.query(InspectionRun)
            .filter(
                InspectionRun.id == inspection_id
            )
            .first()
        )

    @staticmethod
    def get_findings(
        db: Session,
        inspection_id,
    ) -> list[InspectionFinding]:
        """
        Retrieve all findings belonging to an inspection.
        """

        return (
            db.query(InspectionFinding)
            .filter(
                InspectionFinding.inspection_id
                == inspection_id
            )
            .order_by(
                InspectionFinding.created_at.asc()
            )
            .all()
        )

    @staticmethod
    def _build_summary(
        inspection_result: dict[str, Any],
    ) -> str:
        """
        Build a concise human-readable inspection summary.
        """

        status = inspection_result.get(
            "status",
            "UNKNOWN",
        )

        finding_count = inspection_result.get(
            "finding_count",
            0,
        )

        highest_severity = inspection_result.get(
            "highest_severity",
        )

        if finding_count == 0:
            return (
                "Inspection completed successfully. "
                "No data-quality or schema-drift findings "
                "were detected."
            )

        if highest_severity:
            return (
                f"Inspection detected {finding_count} "
                f"finding(s). Highest severity: "
                f"{highest_severity}. "
                f"Overall status: {status}."
            )

        return (
            f"Inspection detected {finding_count} "
            f"finding(s). Overall status: {status}."
        )