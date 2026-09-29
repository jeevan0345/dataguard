from app.agents.inspector.schema_drift import SchemaDriftAgent


def print_findings(result):
    if not result["findings"]:
        print("No findings detected.")
        return

    for index, finding in enumerate(
        result["findings"],
        start=1
    ):
        print(f"\nFinding #{index}")
        print(f"Type: {finding['type']}")
        print(f"Severity: {finding['severity']}")
        print(f"Message: {finding['message']}")
        print(f"Evidence: {finding['evidence']}")


def main():
    print("=" * 70)
    print("DATAGUARD SCHEMA DRIFT AGENT TEST")
    print("=" * 70)

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
    # Actual schema with deliberate drift
    #
    # 1. order_status changed from string → integer
    # 2. amount was removed
    # 3. customer_email was added
    # ---------------------------------------------------------
    actual_schema = {
        "order_id": "string",
        "customer_id": "string",
        "order_status": "integer",
        "order_date": "datetime",
        "customer_email": "string",
    }

    print("\nExpected Schema:")
    for column, data_type in expected_schema.items():
        print(f"  {column}: {data_type}")

    print("\nActual Schema:")
    for column, data_type in actual_schema.items():
        print(f"  {column}: {data_type}")

    # ---------------------------------------------------------
    # Run Schema Drift Agent
    # ---------------------------------------------------------
    print("\n[1] Running Schema Drift Agent...")

    agent = SchemaDriftAgent()

    result = agent.inspect(
        expected_schema=expected_schema,
        actual_schema=actual_schema,
    )

    # ---------------------------------------------------------
    # Display result
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("SCHEMA DRIFT RESULT")
    print("=" * 70)

    print(f"Agent: {result['agent']}")
    print(f"Status: {result['status']}")
    print(
        f"Expected Columns: "
        f"{result['expected_column_count']}"
    )
    print(
        f"Actual Columns: "
        f"{result['actual_column_count']}"
    )
    print(
        f"Added Columns: "
        f"{result['added_columns']}"
    )
    print(
        f"Removed Columns: "
        f"{result['removed_columns']}"
    )
    print(
        f"Finding Count: "
        f"{result['finding_count']}"
    )

    # ---------------------------------------------------------
    # Display findings
    # ---------------------------------------------------------
    print("\n" + "-" * 70)
    print("FINDINGS")
    print("-" * 70)

    print_findings(result)

    print("\n" + "=" * 70)
    print("SCHEMA DRIFT TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()