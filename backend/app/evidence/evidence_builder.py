from typing import Any
from app.core.security import compute_canonical_hash, compute_canonical_hmac


class EvidenceBuilder:
    """
    Converts Inspector Agent findings into structured evidence
    that downstream agents can reason over.

    The Evidence Engine also produces cryptographic SHA-256 and HMAC
    signatures guaranteeing tamper-evident audit integrity.
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

        canonical = self.compute_canonical_audit(
            dataset_path=str(inspection_result.get("dataset_path", "")),
            status=str(inspection_result.get("status", "UNKNOWN")),
            highest_severity=inspection_result.get("highest_severity"),
            row_count=int(inspection_result.get("row_count", 0)),
            column_count=int(inspection_result.get("column_count", 0)),
            findings=findings,
        )
        audit_hash, audit_hmac = self.generate_audit_signatures(canonical)

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
            "audit_hash": audit_hash,
            "audit_hmac": audit_hmac,
        }

    @staticmethod
    def compute_canonical_audit(
        dataset_path: str,
        status: str,
        highest_severity: str | None,
        row_count: int,
        column_count: int,
        findings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Builds deterministic normalized audit dictionary for hashing and signing.
        """
        normalized_findings = []
        for f in findings:
            normalized_findings.append({
                "type": str(f.get("type") or f.get("finding_type") or "UNKNOWN"),
                "severity": str(f.get("severity") or "LOW"),
                "column": str(f.get("column") or f.get("column_name") or ""),
                "message": str(f.get("message") or ""),
            })
        normalized_findings.sort(key=lambda x: (x["type"], x["column"], x["severity"], x["message"]))
        return {
            "dataset_path": dataset_path,
            "status": status,
            "highest_severity": highest_severity or "NONE",
            "row_count": row_count,
            "column_count": column_count,
            "finding_count": len(normalized_findings),
            "findings": normalized_findings,
        }

    @staticmethod
    def generate_audit_signatures(
        canonical_audit: dict[str, Any],
    ) -> tuple[str, str]:
        """
        Returns (sha256_hash, hmac_sha256_signature).
        """
        return compute_canonical_hash(canonical_audit), compute_canonical_hmac(canonical_audit)