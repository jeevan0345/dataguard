from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.anomaly import analyze_run
from app.audit.finding import generate_findings
from app.audit.models import ETLFinding


class ETLFindingService:
    """
    Service responsible for generating and persisting
    ETL anomaly findings.
    """

    @staticmethod
    def generate_and_save_findings(
        db: Session,
        run_id: UUID,
    ) -> list[ETLFinding]:
        """
        Analyze an ETL run, generate structured findings,
        replace any existing findings for that run, and
        persist the latest findings.
        """

        # -------------------------------------------------
        # 1. Analyze the ETL run
        # -------------------------------------------------

        anomaly_result = analyze_run(
            db=db,
            run_id=str(run_id),
        )

        # -------------------------------------------------
        # 2. Generate structured findings
        # -------------------------------------------------

        findings = generate_findings(
            anomaly_result
        )

        # -------------------------------------------------
        # 3. Remove previous findings for this run
        # -------------------------------------------------

        db.query(ETLFinding).filter(
            ETLFinding.run_id == run_id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # 4. Save the latest findings
        # -------------------------------------------------

        saved_findings: list[ETLFinding] = []

        for finding in findings:

            db_finding = ETLFinding(
                run_id=run_id,
                metric=finding.metric,
                finding_type=finding.finding_type,
                severity=finding.severity,
                actual_value=finding.actual_value,
                expected_average=finding.expected_average,
                lower_bound=finding.lower_bound,
                upper_bound=finding.upper_bound,
                deviation=finding.deviation,
                evidence=finding.evidence,
                likely_area=finding.likely_area,
                explanation=finding.explanation,
            )

            db.add(db_finding)

            saved_findings.append(
                db_finding
            )

        # -------------------------------------------------
        # 5. Commit transaction
        # -------------------------------------------------

        db.commit()

        # Refresh objects so generated UUIDs and timestamps
        # are available in the response.
        for finding in saved_findings:
            db.refresh(finding)

        return saved_findings