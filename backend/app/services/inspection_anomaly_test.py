from app.services.inspection_service import InspectionService


def main():
    print("=" * 70)
    print("DATAGUARD INSPECTION SERVICE ANOMALY TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # Deliberately problematic dataset
    # ---------------------------------------------------------
    rows = [
        {
            "order_id": "1001",
            "customer_id": "C001",
            "order_status": "delivered",
            "amount": "500",
            "order_date": "2026-09-01",
        },
        {
            "order_id": "1002",
            "customer_id": None,
            "order_status": "delivered",
            "amount": "750",
            "order_date": "2026-09-02",
        },
        {
            "order_id": "1003",
            "customer_id": None,
            "order_status": "delivered",
            "amount": "900",
            "order_date": "2026-09-03",
        },
        {
            "order_id": "1001",
            "customer_id": "C001",
            "order_status": "delivered",
            "amount": "500",
            "order_date": "2026-09-01",
        },
        {
            "order_id": "1001",
            "customer_id": "C001",
            "order_status": "delivered",
            "amount": "500",
            "order_date": "2026-09-01",
        },
    ]

    # ---------------------------------------------------------
    # Expected schema
    # ---------------------------------------------------------
    expected_schema = {
        "order_id": "string",
        "customer_id": "string",
        "order_status": "string",
        "amount": "float",
        "order_date": "datetime",
    }

    # ---------------------------------------------------------
    # Deliberately create schema drift
    #
    # amount:
    #   removed
    #
    # customer_email:
    #   added
    #
    # order_status:
    #   string → integer
    # ---------------------------------------------------------
    rows_with_schema_drift = [
        {
            "order_id": "1001",
            "customer_id": "C001",
            "order_status": 1,
            "order_date": "2026-09-01",
            "customer_email": "customer1@example.com",
        },
        {
            "order_id": "1002",
            "customer_id": None,
            "order_status": 1,
            "order_date": "2026-09-02",
            "customer_email": "customer2@example.com",
        },
        {
            "order_id": "1003",
            "customer_id": None,
            "order_status": 1,
            "order_date": "2026-09-03",
            "customer_email": "customer3@example.com",
        },
        {
            "order_id": "1001",
            "customer_id": "C001",
            "order_status": 1,
            "order_date": "2026-09-01",
            "customer_email": "customer1@example.com",
        },
        {
            "order_id": "1001",
            "customer_id": "C001",
            "order_status": 1,
            "order_date": "2026-09-01",
            "customer_email": "customer1@example.com",
        },
    ]

    # ---------------------------------------------------------
    # Create service
    # ---------------------------------------------------------
    service = InspectionService()

    # ---------------------------------------------------------
    # TEST 1 — Data Quality
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("TEST 1 — DATA QUALITY")
    print("=" * 70)

    result = service.inspect_rows(
        rows=rows,
        expected_schema=expected_schema,
        dataset_path="test/data_quality_dataset",
    )

    inspection = result["inspection"]

    print(f"\nRows: {result['row_count']}")
    print(f"Columns: {result['column_count']}")
    print(f"Status: {inspection['status']}")
    print(f"Highest Severity: {inspection['highest_severity']}")
    print(f"Finding Count: {inspection['finding_count']}")

    print("\nFindings:")

    for index, finding in enumerate(
        inspection["findings"],
        start=1,
    ):
        print(f"\nFinding #{index}")
        print(f"Type: {finding['type']}")
        print(f"Severity: {finding['severity']}")
        print(f"Message: {finding['message']}")
        print(f"Evidence: {finding['evidence']}")

    # ---------------------------------------------------------
    # TEST 2 — Schema Drift + Data Quality
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("TEST 2 — SCHEMA DRIFT + DATA QUALITY")
    print("=" * 70)

    result = service.inspect_rows(
        rows=rows_with_schema_drift,
        expected_schema=expected_schema,
        dataset_path="test/schema_drift_dataset",
    )

    inspection = result["inspection"]

    print(f"\nRows: {result['row_count']}")
    print(f"Columns: {result['column_count']}")
    print(f"Status: {inspection['status']}")
    print(f"Highest Severity: {inspection['highest_severity']}")
    print(f"Finding Count: {inspection['finding_count']}")

    print("\nInferred Schema:")

    for column, data_type in result["actual_schema"].items():
        print(f"  {column}: {data_type}")

    print("\nFindings:")

    for index, finding in enumerate(
        inspection["findings"],
        start=1,
    ):
        print(f"\nFinding #{index}")
        print(f"Type: {finding['type']}")
        print(f"Severity: {finding['severity']}")
        print(f"Message: {finding['message']}")
        print(f"Evidence: {finding['evidence']}")

    # ---------------------------------------------------------
    # Final
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("INSPECTION SERVICE ANOMALY TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()