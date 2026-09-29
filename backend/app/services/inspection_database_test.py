from uuid import UUID

from app.database.session import SessionLocal
from app.services.inspection_finding_service import (
    InspectionFindingService,
)


INSPECTION_ID = "c8ecb0e1-de45-4044-950c-9ce9caf0d743"


def main():
    print("=" * 70)
    print("DATAGUARD INSPECTION DATABASE VERIFICATION")
    print("=" * 70)

    db = SessionLocal()

    try:
        inspection_id = UUID(INSPECTION_ID)

        print("\n[1] Searching PostgreSQL...")

        inspection = InspectionFindingService.get_inspection(
            db=db,
            inspection_id=inspection_id,
        )

        if inspection is None:
            print("\nERROR: Inspection was not found in PostgreSQL.")
            return

        print("\nInspection found successfully.")

        print(f"Inspection ID: {inspection.id}")
        print(f"Dataset: {inspection.dataset_path}")
        print(f"Status: {inspection.status}")
        print(
            f"Highest Severity: "
            f"{inspection.highest_severity}"
        )
        print(f"Rows: {inspection.row_count}")
        print(f"Columns: {inspection.column_count}")
        print(f"Findings: {inspection.finding_count}")
        print(f"Summary: {inspection.summary}")

        print("\n[2] Reading persisted findings...")

        findings = InspectionFindingService.get_findings(
            db=db,
            inspection_id=inspection_id,
        )

        print(
            f"Persisted finding records: "
            f"{len(findings)}"
        )

        if len(findings) != inspection.finding_count:
            print(
                "\nERROR: Finding count mismatch."
            )
            print(
                f"Inspection says: "
                f"{inspection.finding_count}"
            )
            print(
                f"Database returned: "
                f"{len(findings)}"
            )
            return

        print("\n[3] Verification checks...")

        checks = {
            "Inspection ID matches": (
                str(inspection.id) == INSPECTION_ID
            ),
            "Dataset path matches": (
                inspection.dataset_path
                == "olist/olist_orders_dataset.csv"
            ),
            "Status is HEALTHY": (
                inspection.status == "HEALTHY"
            ),
            "Row count is 99441": (
                inspection.row_count == 99441
            ),
            "Column count is 8": (
                inspection.column_count == 8
            ),
            "Finding count is 0": (
                inspection.finding_count == 0
            ),
            "No persisted findings": (
                len(findings) == 0
            ),
        }

        all_passed = True

        for check_name, passed in checks.items():
            status = "PASS" if passed else "FAIL"

            print(
                f"{status}: {check_name}"
            )

            if not passed:
                all_passed = False

        print("\n" + "=" * 70)

        if all_passed:
            print(
                "INSPECTION DATABASE VERIFICATION PASSED"
            )
        else:
            print(
                "INSPECTION DATABASE VERIFICATION FAILED"
            )

        print("=" * 70)

    except Exception as exc:
        db.rollback()

        print("\n" + "=" * 70)
        print(
            "INSPECTION DATABASE VERIFICATION FAILED"
        )
        print("=" * 70)
        print(f"Error: {exc}")

        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()