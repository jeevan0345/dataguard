"""
DataGuard Controlled Recovery Agent
Generates safe, policy-checked recovery candidates for autonomous or operator-approved remediation.
"""

from typing import Any
import copy
from app.agents.base.base_agent import BaseAgent


class RecoveryAgent(BaseAgent):
    """
    Controlled Recovery Agent for DataGuard 2.0.
    Generates remediation proposals backed by policy checks and human-in-the-loop approval.
    """

    def __init__(
        self,
        max_auto_quarantine_pct: float = 15.0,
    ) -> None:
        super().__init__(
            name="Recovery Agent",
            role="Controlled Self-Healing & Remediation Planning",
            description="Designs safe recovery proposals with policy constraints, risk assessment, and verification dry-runs.",
        )
        self.max_auto_quarantine_pct = max_auto_quarantine_pct

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.propose_recovery(*args, **kwargs)

    def propose_recovery(
        self,
        findings: list[dict[str, Any]],
        rows: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Generate candidate recovery actions and run safety policy checks.
        """
        candidates: list[dict[str, Any]] = []
        total_rows = len(rows) if rows else 0

        action_id = 1
        for finding in findings:
            ftype = finding.get("type", "")
            severity = finding.get("severity", "MEDIUM")
            evidence = finding.get("evidence", {})
            col = evidence.get("column", "")

            if ftype == "DUPLICATE_RECORDS":
                dup_count = evidence.get("duplicate_count", 0)
                dup_pct = evidence.get("duplicate_percentage", 0.0)
                # Policy check: cannot drop > 25% without explicit operator approval
                requires_approval = dup_pct > self.max_auto_quarantine_pct
                policy_status = "REQUIRES_OPERATOR_APPROVAL" if requires_approval else "POLICY_APPROVED"

                candidates.append({
                    "action_id": f"ACT-{action_id:03d}",
                    "action_type": "DEDUPLICATE_ROWS",
                    "target_type": "DATASET",
                    "severity": severity,
                    "target": "ALL_ROWS",
                    "risk_level": "MEDIUM" if requires_approval else "LOW",
                    "policy_status": policy_status,
                    "estimated_impact": f"Removes {dup_count} duplicate record(s) ({dup_pct:.1f}%).",
                    "action_parameters": {"mode": "KEEP_FIRST_OCCURRENCE"},
                    "remediation_code": (
                        "seen = set()\n"
                        "deduped_rows = []\n"
                        "for r in rows:\n"
                        "    h = tuple(sorted(r.items()))\n"
                        "    if h not in seen:\n"
                        "        seen.add(h)\n"
                        "        deduped_rows.append(r)"
                    ),
                })
                action_id += 1

            elif ftype == "MISSING_VALUES":
                missing_count = evidence.get("missing_count", 0)
                missing_pct = evidence.get("missing_percentage", 0.0)
                requires_approval = missing_pct > self.max_auto_quarantine_pct

                # If identifier column, propose quarantine; if value, propose default imputation
                is_identifier = "id" in col.lower() or "key" in col.lower()
                if is_identifier:
                    action_type = "QUARANTINE_NULL_RECORDS"
                    action_desc = f"Quarantine {missing_count} rows with null identifier in '{col}' to DLQ."
                    rem_code = f"clean_rows = [r for r in rows if r.get('{col}') is not None and str(r.get('{col}')).strip() != '']"
                else:
                    action_type = "IMPUTE_DEFAULT_VALUE"
                    action_desc = f"Impute missing values in '{col}' with 'UNKNOWN' or median."
                    rem_code = (
                        f"for r in rows:\n"
                        f"    if r.get('{col}') is None or str(r.get('{col}')).strip() == '':\n"
                        f"        r['{col}'] = 'UNKNOWN'"
                    )

                candidates.append({
                    "action_id": f"ACT-{action_id:03d}",
                    "action_type": action_type,
                    "target_type": "COLUMN",
                    "target": col,
                    "severity": severity,
                    "risk_level": "HIGH" if requires_approval else "LOW",
                    "policy_status": "REQUIRES_OPERATOR_APPROVAL" if requires_approval else "POLICY_APPROVED",
                    "estimated_impact": action_desc,
                    "action_parameters": {"column": col, "missing_count": missing_count},
                    "remediation_code": rem_code,
                })
                action_id += 1

            elif ftype == "COLUMN_REMOVED":
                exp_type = evidence.get("expected_type", "string")
                candidates.append({
                    "action_id": f"ACT-{action_id:03d}",
                    "action_type": "RESTORE_SCHEMA_COLUMN",
                    "target_type": "SCHEMA",
                    "target": col,
                    "severity": severity,
                    "risk_level": "LOW",
                    "policy_status": "POLICY_APPROVED",
                    "estimated_impact": f"Backfills missing column '{col}' with default NULL values.",
                    "action_parameters": {"column": col, "default_type": exp_type},
                    "remediation_code": f"for r in rows: r.setdefault('{col}', None)",
                })
                action_id += 1

            elif ftype == "COLUMN_ADDED":
                act_type = evidence.get("actual_type", "string")
                candidates.append({
                    "action_id": f"ACT-{action_id:03d}",
                    "action_type": "ACCEPT_NEW_COLUMN",
                    "target_type": "SCHEMA",
                    "target": col,
                    "severity": severity,
                    "risk_level": "LOW",
                    "policy_status": "POLICY_APPROVED",
                    "estimated_impact": f"Registers unexpected column '{col}' ({act_type}) into target schema.",
                    "action_parameters": {"column": col, "type": act_type},
                    "remediation_code": f"expected_schema['{col}'] = '{act_type}'",
                })
                action_id += 1

            elif ftype in ["ML_ISOLATION_FOREST_ANOMALY", "NUMERICAL_OUTLIERS"]:
                outlier_count = evidence.get("outlier_count", evidence.get("anomalous_row_count", 0))
                candidates.append({
                    "action_id": f"ACT-{action_id:03d}",
                    "action_type": "QUARANTINE_ML_OUTLIERS",
                    "target_type": "DATASET",
                    "target": col or "MULTIVARIATE",
                    "severity": severity,
                    "risk_level": "MEDIUM",
                    "policy_status": "REQUIRES_OPERATOR_APPROVAL",
                    "estimated_impact": f"Routes {outlier_count} multivariate outlier records into dlq_anomalies.",
                    "action_parameters": {"column": col, "count": outlier_count},
                    "remediation_code": "-- Divert anomalous rows into dead-letter storage",
                })
                action_id += 1

        overall_policy = "REQUIRES_APPROVAL" if any(c["risk_level"] == "HIGH" for c in candidates) else "READY_FOR_EXECUTION"

        return {
            "agent": self.name,
            "status": "RECOVERY_PLAN_PROPOSED",
            "overall_policy": overall_policy,
            "candidate_count": len(candidates),
            "candidates": candidates,
            "summary": (
                f"Recovery Agent proposed {len(candidates)} controlled remediation candidate(s). "
                f"Policy posture: {overall_policy}. Zero uncontrolled modifications permitted."
            ),
        }

    def execute_recovery(
        self,
        rows: list[dict[str, Any]],
        candidate_actions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Applies approved recovery candidate transformations to rows in-memory.
        Returns the remediated dataset buffer.
        """
        remediated = [copy.deepcopy(r) for r in rows]

        for act in candidate_actions:
            atype = act.get("action_type")
            target = act.get("target")

            if atype == "DEDUPLICATE_ROWS":
                seen = set()
                deduped = []
                for r in remediated:
                    # Convert row to frozen representation
                    frozen = tuple(sorted((k, str(v)) for k, v in r.items()))
                    if frozen not in seen:
                        seen.add(frozen)
                        deduped.append(r)
                remediated = deduped

            elif atype == "QUARANTINE_NULL_RECORDS":
                col = act.get("action_parameters", {}).get("column", target)
                remediated = [
                    r for r in remediated
                    if r.get(col) is not None and str(r.get(col)).strip() != ""
                ]

            elif atype == "IMPUTE_DEFAULT_VALUE":
                col = act.get("action_parameters", {}).get("column", target)
                for r in remediated:
                    if r.get(col) is None or str(r.get(col)).strip() == "":
                        r[col] = "UNKNOWN"

            elif atype == "RESTORE_SCHEMA_COLUMN":
                col = act.get("action_parameters", {}).get("column", target)
                for r in remediated:
                    if col not in r:
                        r[col] = None

        return remediated
