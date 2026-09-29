from app.agents.inspector.data_quality import DataQualityAgent


def main():
    print("=" * 70)
    print("DATAGUARD DATA QUALITY AGENT TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # Test dataset
    # ---------------------------------------------------------
    rows = [
        {
            "order_id": "1001",
            "customer_id": "C001",
            "amount": "500"
        },
        {
            "order_id": "1002",
            "customer_id": None,
            "amount": "750"
        },
        {
            "order_id": "1003",
            "customer_id": None,
            "amount": "900"
        },
        {
            "order_id": "1001",
            "customer_id": "C001",
            "amount": "500"
        },
        {
            "order_id": "1001",
            "customer_id": "C001",
            "amount": "500"
        },
    ]

    print(f"\nTest rows: {len(rows)}")

    # ---------------------------------------------------------
    # Run Data Quality Agent
    # ---------------------------------------------------------
    agent = DataQualityAgent()

    result = agent.inspect(rows)

    # ---------------------------------------------------------
    # Display result
    # ---------------------------------------------------------
    print("\n" + "=" * 70)
    print("DATA QUALITY RESULT")
    print("=" * 70)

    print(f"Agent: {result['agent']}")
    print(f"Status: {result['status']}")
    print(f"Rows: {result['row_count']}")
    print(f"Finding Count: {result['finding_count']}")

    # ---------------------------------------------------------
    # Display findings
    # ---------------------------------------------------------
    print("\n" + "-" * 70)
    print("FINDINGS")
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
    print("DATA QUALITY TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()