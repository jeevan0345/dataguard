from typing import Any


class EvidenceBuilder:
    """
    Converts Inspector Agent findings into structured evidence
    that downstream agents can reason over.

    The Evidence Engine does not decide the root cause.
    It only organizes facts and evidence.
    """

    def __init__(self) -> None:
        self.engine_name = "Evidence Engine"

    def build(
        self,
        inspection_result: dict[str, Any],
    ) -> dict[str, Any]:

        findings = inspection_result.get("findings", [])

        evidence_items = []

        for index, finding in enumerate(findings, start=1):

            evidence = finding.get("evidence", {})

            evidence_items.append(
                {
                    "evidence_id": f"E{index}",
                    "finding_type": finding.get(
                        "type",
                        "UNKNOWN",
                    ),
                    "severity": finding.get(
                        "severity",
                        "UNKNOWN",
                    ),
                    "message": finding.get(
                        "message",
                        "",
                    ),
                    "evidence": evidence,
                }
            )

        return {
            "engine": self.engine_name,
            "status": (
                "EVIDENCE_AVAILABLE"
                if evidence_items
                else "NO_EVIDENCE"
            ),
            "finding_count": len(findings),
            "evidence_count": len(evidence_items),
            "evidence": evidence_items,
        }