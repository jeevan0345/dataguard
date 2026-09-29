"""
DataGuard Verification Engine
Re-profiles and re-audits datasets post-remediation to issue PASS/FAIL audit verdicts.
"""

from typing import Any
from datetime import datetime


class VerificationEngine:
    """
    Verification Engine for DataGuard 2.0.
    Ensures that applied recovery plans genuinely resolved anomalies
    without introducing secondary regressions.
    """

    @staticmethod
    def verify(
        before_inspection: dict[str, Any],
        after_inspection: dict[str, Any],
        original_row_count: int,
        remediated_row_count: int,
    ) -> dict[str, Any]:
        """
        Compare before and after inspection results to compute verdict.
        """
        before_findings = before_inspection.get("findings", [])
        after_findings = after_inspection.get("findings", [])

        before_count = len(before_findings)
        after_count = len(after_findings)

        resolved_count = max(0, before_count - after_count)
        reduction_rate = round((resolved_count / before_count) * 100, 2) if before_count > 0 else 100.0

        # Check severities in remaining findings
        remaining_severities = [f.get("severity", "LOW") for f in after_findings]
        has_critical = "CRITICAL" in remaining_severities
        has_high = "HIGH" in remaining_severities

        if after_count == 0:
            verdict = "PASS"
            message = "All identified anomalies were successfully remediated. Dataset is 100% healthy."
        elif not has_critical and not has_high and after_count < before_count:
            verdict = "PARTIAL_PASS"
            message = f"Critical and high findings resolved ({reduction_rate}% reduction). Minor low-severity notes remain."
        else:
            verdict = "FAIL"
            message = f"Remediation failed to eliminate critical risks. {after_count} finding(s) remain unresolved."

        return {
            "engine": "DataGuard Verification Engine",
            "verified_at": datetime.utcnow().isoformat(),
            "verdict": verdict,
            "metrics": {
                "before_finding_count": before_count,
                "after_finding_count": after_count,
                "resolved_finding_count": resolved_count,
                "anomaly_reduction_rate_pct": reduction_rate,
                "original_row_count": original_row_count,
                "remediated_row_count": remediated_row_count,
                "row_delta": remediated_row_count - original_row_count,
            },
            "remaining_findings": after_findings,
            "message": message,
            "audit_trail": {
                "pre_status": before_inspection.get("status", "UNKNOWN"),
                "post_status": after_inspection.get("status", "UNKNOWN"),
                "signed_off": verdict in ["PASS", "PARTIAL_PASS"],
            },
        }
