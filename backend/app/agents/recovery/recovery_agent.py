"""
DataGuard Controlled Recovery Agent
Generates safe, policy-checked recovery candidates for autonomous or operator-approved remediation.
"""

from typing import Any
import copy
from collections import Counter
import numpy as np
from app.agents.base.base_agent import BaseAgent
from app.ml.isolation_forest import IsolationForestDetector


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
            col = finding.get("column") or evidence.get("column", "")

            if ftype == "DUPLICATE_RECORDS":
                dup_count = evidence.get("duplicate_count", 0)
                dup_pct = evidence.get("duplicate_percentage", 0.0)
                requires_approval = dup_pct > self.max_auto_quarantine_pct
                policy_status = "REQUIRES_OPERATOR_APPROVAL" if requires_approval else "POLICY_APPROVED"
                risk_level = "MEDIUM" if requires_approval else "LOW"
                required_role = "ADMIN" if requires_approval else "DATA_ENGINEER"

                candidates.append({
                    "action_id": f"ACT-{action_id:03d}",
                    "action_type": "DEDUPLICATE_ROWS",
                    "target_type": "DATASET",
                    "severity": severity,
                    "target": "ALL_ROWS",
                    "risk_level": risk_level,
                    "policy_status": policy_status,
                    "required_role": required_role,
                    "estimated_impact": f"Removes {dup_count} duplicate record(s) ({dup_pct:.1f}%).",
                    "action_parameters": {"mode": "KEEP_FIRST_OCCURRENCE", "count": dup_count},
                    "remediation_code": (
                        "seen = set()\n"
                        "deduped_rows = []\n"
                        "for r in rows:\n"
                        "    h = tuple(sorted((k, str(v) if v is not None else '') for k, v in r.items()))\n"
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
                risk_level = "HIGH" if requires_approval else "LOW"
                policy_status = "REQUIRES_OPERATOR_APPROVAL" if requires_approval else "POLICY_APPROVED"
                required_role = "ADMIN" if requires_approval else "DATA_ENGINEER"

                # If identifier column, propose quarantine; if value, propose domain-aware default imputation
                is_identifier = "id" in col.lower() or "key" in col.lower()
                if is_identifier:
                    action_type = "QUARANTINE_NULL_RECORDS"
                    action_desc = f"Quarantine {missing_count} rows with null identifier in '{col}' to DLQ."
                    rem_code = f"clean_rows = [r for r in rows if r.get('{col}') is not None and str(r.get('{col}')).strip() != '']"
                    act_params: dict[str, Any] = {"column": col, "missing_count": missing_count}
                else:
                    action_type = "IMPUTE_DEFAULT_VALUE"
                    # Determine strategy and impute value dynamically from data
                    is_numeric = False
                    strategy = "MODE"
                    impute_val: Any = "UNKNOWN"

                    if rows:
                        valid_nums: list[float] = []
                        valid_strs: list[str] = []
                        for r in rows:
                            v = r.get(col)
                            if v is not None and str(v).strip() != "" and str(v).strip().upper() != "UNKNOWN":
                                try:
                                    fv = float(v)
                                    valid_nums.append(fv)
                                except (ValueError, TypeError):
                                    valid_strs.append(str(v).strip())

                        if valid_nums and len(valid_nums) >= len(valid_strs):
                            is_numeric = True
                            med = float(np.median(valid_nums))
                            if all(float(x).is_integer() for x in valid_nums):
                                impute_val = int(round(med))
                            else:
                                impute_val = round(med, 2)
                            strategy = "MEDIAN"
                        elif valid_strs:
                            impute_val = Counter(valid_strs).most_common(1)[0][0]
                            strategy = "MODE"

                    action_desc = f"Imputes {missing_count} missing value(s) in '{col}' using {strategy.lower()} ({repr(impute_val)})."
                    rem_code = (
                        f"for r in rows:\n"
                        f"    if r.get('{col}') is None or str(r.get('{col}')).strip() == '':\n"
                        f"        r['{col}'] = {repr(impute_val)}"
                    )
                    act_params = {
                        "column": col,
                        "missing_count": missing_count,
                        "strategy": strategy,
                        "impute_value": impute_val,
                    }

                candidates.append({
                    "action_id": f"ACT-{action_id:03d}",
                    "action_type": action_type,
                    "target_type": "COLUMN",
                    "target": col,
                    "severity": severity,
                    "risk_level": risk_level,
                    "policy_status": policy_status,
                    "required_role": required_role,
                    "estimated_impact": action_desc,
                    "action_parameters": act_params,
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
                    "required_role": "DATA_ENGINEER",
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
                    "required_role": "DATA_ENGINEER",
                    "estimated_impact": f"Registers unexpected column '{col}' ({act_type}) into target schema.",
                    "action_parameters": {"column": col, "type": act_type},
                    "remediation_code": f"expected_schema['{col}'] = '{act_type}'",
                })
                action_id += 1

            elif ftype in ["ML_ISOLATION_FOREST_ANOMALY", "NUMERICAL_OUTLIERS"]:
                outlier_count = evidence.get("outlier_count", evidence.get("anomalous_row_count", 0))
                anom_indices = evidence.get("sample_anomalous_indices", []) or evidence.get("anomalous_row_indices", [])
                candidates.append({
                    "action_id": f"ACT-{action_id:03d}",
                    "action_type": "QUARANTINE_ML_OUTLIERS",
                    "target_type": "DATASET",
                    "target": col or "MULTIVARIATE",
                    "severity": severity,
                    "risk_level": "MEDIUM",
                    "policy_status": "REQUIRES_OPERATOR_APPROVAL",
                    "required_role": "ADMIN",
                    "estimated_impact": f"Quarantines {outlier_count} multivariate outlier records into dlq_anomalies.",
                    "action_parameters": {
                        "column": col or "MULTIVARIATE",
                        "count": outlier_count,
                        "anomalous_indices": anom_indices,
                    },
                    "remediation_code": (
                        "# Quarantine multivariate outliers detected by Isolation Forest\n"
                        "detector = IsolationForestDetector()\n"
                        "outlier_indices = set(detector.detect(rows).get('anomalous_row_indices', []))\n"
                        "clean_rows = [r for idx, r in enumerate(rows) if idx not in outlier_indices]"
                    ),
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
                    frozen = tuple(sorted((k, str(v).strip() if v is not None else "") for k, v in r.items()))
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
                impute_val = act.get("action_parameters", {}).get("impute_value")

                # If impute_val is None or "UNKNOWN", compute dynamically based on current data
                if impute_val is None or impute_val == "UNKNOWN":
                    valid_nums: list[float] = []
                    valid_strs: list[str] = []
                    for r in remediated:
                        v = r.get(col)
                        if v is not None and str(v).strip() != "" and str(v).strip().upper() != "UNKNOWN":
                            try:
                                fv = float(v)
                                valid_nums.append(fv)
                            except (ValueError, TypeError):
                                valid_strs.append(str(v).strip())

                    if valid_nums and len(valid_nums) >= len(valid_strs):
                        med = float(np.median(valid_nums))
                        if all(float(x).is_integer() for x in valid_nums):
                            impute_val = int(round(med))
                        else:
                            impute_val = round(med, 2)
                    elif valid_strs:
                        impute_val = Counter(valid_strs).most_common(1)[0][0]
                    else:
                        impute_val = "UNKNOWN"

                for r in remediated:
                    if r.get(col) is None or str(r.get(col)).strip() == "" or str(r.get(col)).strip().upper() == "UNKNOWN":
                        r[col] = impute_val

            elif atype == "QUARANTINE_ML_OUTLIERS":
                detector = IsolationForestDetector()
                iso_res = detector.detect(remediated)
                outlier_indices = set(iso_res.get("anomalous_row_indices", []))
                if outlier_indices:
                    remediated = [r for idx, r in enumerate(remediated) if idx not in outlier_indices]

            elif atype == "RESTORE_SCHEMA_COLUMN":
                col = act.get("action_parameters", {}).get("column", target)
                for r in remediated:
                    if col not in r:
                        r[col] = None

        return remediated
