from app.database.session import SessionLocal
from app.services.inspection_finding_service import (
    InspectionFindingService,
)


def main():
    print("=" * 70)
    print("DATAGUARD INSPECTION FINDING SERVICE TEST")
    print("=" * 70)

    inspection_result = {
        "status": "ANOMALY_DETECTED",
        "highest_severity": "CRITICAL",
        "finding_count": 2,
        "findings": [
            {
                "type": "MISSING_VALUES",
                "severity": "HIGH",
                "message": (
                    "Column 'customer_id' contains "
                    "2 missing value(s)."
                ),
                "evidence": {
                    "column": "customer_id",
                    "missing_count": 2,
                    "missing_percentage": 40.0,
                    "total_rows": 5,
                },
            },
            {
                "type": "DUPLICATE_RECORDS",
                "severity": "CRITICAL",
                "message": (
                    "Detected 2 duplicate record(s)."
                ),
                "evidence": {
                    "duplicate_count": 2,
                    "duplicate_percentage": 40.0,
                    "total_rows": 5,
                },
            },
        ],
    }

    db = SessionLocal()

    try:
        print("\n[1] Saving inspection...")

        inspection = (
            InspectionFindingService.save_inspection(
                db=db,
                dataset_path=(
                    "test/inspection_persistence_dataset"
                ),
                inspection_result=inspection_result,
                row_count=5,
                column_count=5,
            )
        )

        print("\nInspection saved successfully.")

        print(f"Inspection ID: {inspection.id}")
        print(f"Dataset: {inspection.dataset_path}")
        print(f"Status: {inspection.status}")
        print(
            f"Highest Severity: "
            f"{inspection.highest_severity}"
        )
        print(
            f"Finding Count: "
            f"{inspection.finding_count}"
        )
        print(f"Summary: {inspection.summary}")

        print("\n[2] Reading inspection from database...")

        saved_inspection = (
            InspectionFindingService.get_inspection(
                db=db,
                inspection_id=inspection.id,
            )
        )

        if saved_inspection is None:
            print("ERROR: Inspection was not found.")
            return

        print(
            f"Retrieved inspection: "
            f"{saved_inspection.id}"
        )

        print("\n[3] Reading findings from database...")

        findings = (
            InspectionFindingService.get_findings(
                db=db,
                inspection_id=inspection.id,
            )
        )

        print(
            f"Retrieved findings: "
            f"{len(findings)}"
        )

        for index, finding in enumerate(
            findings,
            start=1,
        ):
            print(f"\nFinding #{index}")
            print(f"ID: {finding.id}")
            print(
                f"Type: "
                f"{finding.finding_type}"
            )
            print(
                f"Severity: "
                f"{finding.severity}"
            )
            print(
                f"Message: "
                f"{finding.message}"
            )
            print(
                f"Evidence: "
                f"{finding.evidence}"
            )
            print(
                f"Column: "
                f"{finding.column_name}"
            )

        print("\n" + "=" * 70)
        print("INSPECTION PERSISTENCE TEST PASSED")
        print("=" * 70)

    except Exception as exc:
        db.rollback()

        print("\n" + "=" * 70)
        print("INSPECTION PERSISTENCE TEST FAILED")
        print("=" * 70)
        print(f"Error: {exc}")

        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()