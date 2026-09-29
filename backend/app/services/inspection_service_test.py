from app.services.inspection_service import InspectionService


def main():
    print("=" * 70)
    print("DATAGUARD INSPECTION SERVICE TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # Expected schema for Olist orders dataset
    # ---------------------------------------------------------
    expected_schema = {
        "order_id": "string",
        "customer_id": "string",
        "order_status": "string",
        "order_purchase_timestamp": "datetime",
        "order_approved_at": "datetime",
        "order_delivered_carrier_date": "datetime",
        "order_delivered_customer_date": "datetime",
        "order_estimated_delivery_date": "datetime",
    }

    # ---------------------------------------------------------
    # Create service
    # ---------------------------------------------------------
    service = InspectionService()

    # ---------------------------------------------------------
    # Run complete inspection
    # ---------------------------------------------------------
    print("\n[1] Running complete inspection...")

    result = service.inspect_dataset(
        dataset_path="olist/olist_orders_dataset.csv",
        expected_schema=expected_schema,
    )

    # ---------------------------------------------------------
    # Dataset information
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("DATASET INFORMATION")
    print("=" * 70)

    print(f"Dataset: {result['dataset_path']}")
    print(f"Rows: {result['row_count']}")
    print(f"Columns: {result['column_count']}")

    # ---------------------------------------------------------
    # Inferred schema
    # ---------------------------------------------------------
    print("\n" + "-" * 70)
    print("INFERRED SCHEMA")
    print("-" * 70)

    for column, data_type in result["actual_schema"].items():
        print(f"{column}: {data_type}")

    # ---------------------------------------------------------
    # Inspector result
    # ---------------------------------------------------------
    inspection = result["inspection"]

    print("\n" + "=" * 70)
    print("INSPECTION RESULT")
    print("=" * 70)

    print(f"Agent: {inspection['agent']}")
    print(f"Status: {inspection['status']}")
    print(f"Highest Severity: {inspection['highest_severity']}")
    print(f"Finding Count: {inspection['finding_count']}")

    # ---------------------------------------------------------
    # Data Quality
    # ---------------------------------------------------------
    print("\n" + "-" * 70)
    print("DATA QUALITY")
    print("-" * 70)

    data_quality = inspection["data_quality"]

    print(f"Status: {data_quality['status']}")
    print(f"Rows: {data_quality['row_count']}")
    print(f"Findings: {data_quality['finding_count']}")

    # ---------------------------------------------------------
    # Schema Drift
    # ---------------------------------------------------------
    print("\n" + "-" * 70)
    print("SCHEMA DRIFT")
    print("-" * 70)

    schema_drift = inspection["schema_drift"]

    if schema_drift is None:
        print("Schema drift inspection was not performed.")
    else:
        print(f"Status: {schema_drift['status']}")
        print(
            f"Expected Columns: "
            f"{schema_drift['expected_column_count']}"
        )
        print(
            f"Actual Columns: "
            f"{schema_drift['actual_column_count']}"
        )
        print(
            f"Added Columns: "
            f"{schema_drift['added_columns']}"
        )
        print(
            f"Removed Columns: "
            f"{schema_drift['removed_columns']}"
        )
        print(
            f"Findings: "
            f"{schema_drift['finding_count']}"
        )

    # ---------------------------------------------------------
    # Unified findings
    # ---------------------------------------------------------
    print("\n" + "-" * 70)
    print("UNIFIED FINDINGS")
    print("-" * 70)

    findings = inspection["findings"]

    if not findings:
        print("No findings detected.")
    else:
        for index, finding in enumerate(
            findings,
            start=1
        ):
            print(f"\nFinding #{index}")
            print(f"Type: {finding['type']}")
            print(f"Severity: {finding['severity']}")
            print(f"Message: {finding['message']}")
            print(f"Evidence: {finding['evidence']}")

    print("\n" + "=" * 70)
    print("INSPECTION SERVICE TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()