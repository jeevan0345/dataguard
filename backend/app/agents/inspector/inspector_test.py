from app.etl.extractor.dataset_loader import DatasetLoader
from app.etl.extractor.schema_inference import SchemaInference
from app.agents.inspector.inspector_agent import InspectorAgent


def main():
    print("=" * 70)
    print("DATAGUARD INSPECTOR AGENT TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Load the real Olist dataset
    # ---------------------------------------------------------
    print("\n[1] Loading dataset...")

    rows = DatasetLoader.load_dataset(
        "olist/olist_orders_dataset.csv"
    )

    print(f"Rows loaded: {len(rows)}")

    if not rows:
        print("ERROR: Dataset is empty.")
        return

    # ---------------------------------------------------------
    # 2. Infer actual schema
    # ---------------------------------------------------------
    print("\n[2] Inferring actual schema...")

    actual_schema = SchemaInference.infer_schema(rows)

    print("Actual Schema:")

    for column, data_type in actual_schema.items():
        print(f"  {column}: {data_type}")

    # ---------------------------------------------------------
    # 3. Create expected schema
    # ---------------------------------------------------------
    print("\n[3] Creating expected schema...")

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

    print("Expected Schema:")

    for column, data_type in expected_schema.items():
        print(f"  {column}: {data_type}")

    # ---------------------------------------------------------
    # 4. Run Inspector Agent
    # ---------------------------------------------------------
    print("\n[4] Running Inspector Agent...")

    inspector = InspectorAgent()

    result = inspector.inspect(
        rows=rows,
        expected_schema=expected_schema,
        actual_schema=actual_schema,
    )

    # ---------------------------------------------------------
    # 5. Display overall result
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("INSPECTION RESULT")
    print("=" * 70)

    print(f"Agent: {result['agent']}")
    print(f"Status: {result['status']}")
    print(f"Highest Severity: {result['highest_severity']}")
    print(f"Finding Count: {result['finding_count']}")

    # ---------------------------------------------------------
    # 6. Display Data Quality result
    # ---------------------------------------------------------
    print("\n" + "-" * 70)
    print("DATA QUALITY")
    print("-" * 70)

    data_quality = result["data_quality"]

    print(f"Status: {data_quality['status']}")
    print(f"Rows: {data_quality['row_count']}")
    print(f"Findings: {data_quality['finding_count']}")

    for finding in data_quality["findings"]:
        print(f"\nType: {finding['type']}")
        print(f"Severity: {finding['severity']}")
        print(f"Message: {finding['message']}")
        print(f"Evidence: {finding['evidence']}")

    # ---------------------------------------------------------
    # 7. Display Schema Drift result
    # ---------------------------------------------------------
    print("\n" + "-" * 70)
    print("SCHEMA DRIFT")
    print("-" * 70)

    schema_drift = result["schema_drift"]

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

        for finding in schema_drift["findings"]:
            print(f"\nType: {finding['type']}")
            print(f"Severity: {finding['severity']}")
            print(f"Message: {finding['message']}")
            print(f"Evidence: {finding['evidence']}")

    # ---------------------------------------------------------
    # 8. Display all unified findings
    # ---------------------------------------------------------
    print("\n" + "-" * 70)
    print("ALL INSPECTOR FINDINGS")
    print("-" * 70)

    if not result["findings"]:
        print("No findings detected.")
    else:
        for index, finding in enumerate(
            result["findings"],
            start=1
        ):
            print(f"\nFinding #{index}")
            print(f"Type: {finding['type']}")
            print(f"Severity: {finding['severity']}")
            print(f"Message: {finding['message']}")
            print(f"Evidence: {finding['evidence']}")

    print("\n" + "=" * 70)
    print("INSPECTOR TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()