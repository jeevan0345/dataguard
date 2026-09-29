from app.agents.inspector.inspector_agent import InspectorAgent
from app.evidence.evidence_builder import EvidenceBuilder
from app.audit.root_cause import analyze_inspection_evidence


# ---------------------------------------------------------
# Test dataset
# ---------------------------------------------------------

rows = [
    {
        "order_id": "1001",
        "customer_id": "C001",
        "order_status": "1",
        "customer_email": "alice@example.com",
    },
    {
        "order_id": "1002",
        "customer_id": "",
        "order_status": "2",
        "customer_email": "bob@example.com",
    },
    {
        "order_id": "1003",
        "customer_id": "C003",
        "order_status": "3",
        "customer_email": "charlie@example.com",
    },
    {
        "order_id": "1003",
        "customer_id": "C003",
        "order_status": "3",
        "customer_email": "charlie@example.com",
    },
    {
        "order_id": "1004",
        "customer_id": "",
        "order_status": "4",
        "customer_email": "david@example.com",
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
# Actual schema
# ---------------------------------------------------------

actual_schema = {
    "order_id": "string",
    "customer_id": "string",
    "order_status": "integer",
    "customer_email": "string",
}


# ---------------------------------------------------------
# Inspector Agent
# ---------------------------------------------------------

agent = InspectorAgent()

inspection_result = agent.inspect(
    rows=rows,
    expected_schema=expected_schema,
    actual_schema=actual_schema,
)


print()
print("Inspector Agent Test")
print("====================")
print(
    "Status:",
    inspection_result["status"],
)
print(
    "Highest Severity:",
    inspection_result["highest_severity"],
)
print(
    "Finding Count:",
    inspection_result["finding_count"],
)


# ---------------------------------------------------------
# Evidence Engine
# ---------------------------------------------------------

builder = EvidenceBuilder()

evidence_result = builder.build(
    inspection_result
)


print()
print("Evidence Engine Test")
print("====================")
print(
    "Status:",
    evidence_result["status"],
)
print(
    "Finding Count:",
    evidence_result["finding_count"],
)
print(
    "Evidence Count:",
    evidence_result["evidence_count"],
)


for item in evidence_result["evidence"]:
    print(
        item["evidence_id"],
        "→",
        item["finding_type"],
        "→",
        item["severity"],
    )


# ---------------------------------------------------------
# Root Cause Analysis
# ---------------------------------------------------------

root_cause_result = analyze_inspection_evidence(
    evidence_result
)


print()
print("Root Cause Analysis")
print("===================")
print(
    "Finding Count:",
    root_cause_result.finding_count,
)
print(
    "Primary Cause:",
    root_cause_result.primary_cause,
)
print(
    "Overall Confidence:",
    root_cause_result.overall_confidence,
)
print(
    "Summary:",
    root_cause_result.summary,
)


# ---------------------------------------------------------
# Root Cause Candidates
# ---------------------------------------------------------

print()
print("Root Cause Candidates")
print("=====================")

for index, candidate in enumerate(
    root_cause_result.candidates,
    start=1,
):

    print()
    print(
        f"Candidate {index}"
    )

    print(
        "Cause:",
        candidate.cause,
    )

    print(
        "Confidence:",
        candidate.confidence,
    )

    print(
        "Affected Area:",
        candidate.affected_area,
    )

    print(
        "Explanation:",
        candidate.explanation,
    )

    print(
        "Evidence:"
    )

    for evidence in candidate.evidence:
        print(
            "  -",
            evidence,
        )