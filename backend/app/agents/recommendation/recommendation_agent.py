"""
DataGuard Recommendation Agent
Generates evidence-grounded, severity-aware, actionable recommendations for data engineers.
"""

from typing import Any
from app.agents.base.base_agent import BaseAgent


class RecommendationAgent(BaseAgent):
    """
    Recommendation Agent for DataGuard 2.0.
    Transforms audit evidence and root causes into prioritized, actionable engineering fixes.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Recommendation Agent",
            role="Actionable Engineering Advice & Best Practices",
            description="Synthesizes findings into prioritized remediation plans, SQL fixes, and pipeline safeguards.",
        )

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.recommend(*args, **kwargs)

    def recommend(
        self,
        findings: list[dict[str, Any]],
        root_cause_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Produce structured recommendations based on observed findings and RCA.
        """
        recommendations: list[dict[str, Any]] = []

        rec_counter = 1

        for finding in findings:
            ftype = finding.get("type", "")
            severity = finding.get("severity", "MEDIUM")
            evidence = finding.get("evidence", {})
            col = evidence.get("column", "target_column")

            if ftype == "MISSING_VALUES":
                missing_count = evidence.get("missing_count", 0)
                missing_pct = evidence.get("missing_percentage", 0)
                priority = "P0_CRITICAL" if severity == "CRITICAL" else ("P1_HIGH" if severity == "HIGH" else "P2_MEDIUM")

                recommendations.append({
                    "id": f"REC-{rec_counter:03d}",
                    "category": "DATA_QUALITY",
                    "priority": priority,
                    "title": f"Handle Missing Values in Column '{col}'",
                    "finding_ref": ftype,
                    "target_column": col,
                    "rationale": f"Detected {missing_count} null/missing values ({missing_pct}%). Unhandled nulls propagate downstream into broken aggregations and analytics.",
                    "action_type": "IMPUTE_OR_QUARANTINE",
                    "suggested_fix": (
                        f"-- Option A: Quarantine affected records\n"
                        f"INSERT INTO quarantine_{col}_nulls\n"
                        f"SELECT * FROM current_dataset WHERE {col} IS NULL;\n\n"
                        f"-- Option B: Impute with domain default\n"
                        f"UPDATE current_dataset SET {col} = 'UNKNOWN' WHERE {col} IS NULL;"
                    ),
                    "impact": "Prevents downstream null-pointer exceptions and protects analytics reporting.",
                })
                rec_counter += 1

            elif ftype == "DUPLICATE_RECORDS":
                dup_count = evidence.get("duplicate_count", 0)
                dup_pct = evidence.get("duplicate_percentage", 0)

                recommendations.append({
                    "id": f"REC-{rec_counter:03d}",
                    "category": "DATA_INTEGRITY",
                    "priority": "P0_CRITICAL",
                    "title": "Deduplicate Dataset and Enforce Unique Constraints",
                    "finding_ref": ftype,
                    "target_column": "ALL_COLUMNS",
                    "rationale": f"Found {dup_count} duplicate row(s) ({dup_pct}%). Duplicates distort metrics like revenue, active users, and inventory counts.",
                    "action_type": "DEDUPLICATION",
                    "suggested_fix": (
                        f"-- Deduplicate keeping earliest record\n"
                        f"DELETE FROM current_dataset a USING current_dataset b\n"
                        f"WHERE a.ctid < b.ctid AND a.order_id = b.order_id;"
                    ),
                    "impact": "Eliminates inflated KPIs and prevents double-billing or phantom inventory.",
                })
                rec_counter += 1

            elif ftype == "COLUMN_REMOVED":
                removed_col = evidence.get("column", "")
                exp_type = evidence.get("expected_type", "")

                recommendations.append({
                    "id": f"REC-{rec_counter:03d}",
                    "category": "SCHEMA_EVOLUTION",
                    "priority": "P0_CRITICAL",
                    "title": f"Restore or Backfill Missing Column '{removed_col}'",
                    "finding_ref": ftype,
                    "target_column": removed_col,
                    "rationale": f"Expected column '{removed_col}' ({exp_type}) was omitted from source extract. Downstream consumers will fail with column not found errors.",
                    "action_type": "SCHEMA_RESTORATION",
                    "suggested_fix": (
                        f"-- Add column back with safe fallback value\n"
                        f"ALTER TABLE current_dataset ADD COLUMN {removed_col} {exp_type} DEFAULT NULL;\n"
                        f"-- Notify upstream producer team to verify extraction query select list."
                    ),
                    "impact": "Maintains backwards compatibility for downstream pipelines and BI dashboards.",
                })
                rec_counter += 1

            elif ftype == "COLUMN_ADDED":
                added_col = evidence.get("column", "")
                act_type = evidence.get("actual_type", "")

                recommendations.append({
                    "id": f"REC-{rec_counter:03d}",
                    "category": "SCHEMA_EVOLUTION",
                    "priority": "P2_MEDIUM",
                    "title": f"Register New Column '{added_col}' in Schema Registry",
                    "finding_ref": ftype,
                    "target_column": added_col,
                    "rationale": f"New column '{added_col}' ({act_type}) appeared without schema version increment.",
                    "action_type": "SCHEMA_EXPANSION",
                    "suggested_fix": (
                        f"-- Update expected schema definition\n"
                        f"expected_schema['{added_col}'] = '{act_type}';\n"
                        f"-- Update target DDL to persist newly available attributes."
                    ),
                    "impact": "Enables safe capture of new upstream domain attributes.",
                })
                rec_counter += 1

            elif ftype == "COLUMN_TYPE_CHANGED":
                chg_col = evidence.get("column", "")
                exp_t = evidence.get("expected_type", "")
                act_t = evidence.get("actual_type", "")

                recommendations.append({
                    "id": f"REC-{rec_counter:03d}",
                    "category": "SCHEMA_EVOLUTION",
                    "priority": "P1_HIGH",
                    "title": f"Add Explicit Type Cast for '{chg_col}'",
                    "finding_ref": ftype,
                    "target_column": chg_col,
                    "rationale": f"Column '{chg_col}' type shifted from '{exp_t}' to '{act_t}'. May cause silent truncation or parsing failures.",
                    "action_type": "TYPE_CASTING",
                    "suggested_fix": (
                        f"-- Apply safe explicit conversion in ETL transformation stage\n"
                        f"SELECT CAST({chg_col} AS {exp_t}) AS {chg_col} FROM raw_stage;"
                    ),
                    "impact": "Prevents runtime typing exceptions in downstream analytical engines.",
                })
                rec_counter += 1

            elif ftype in ["ML_ISOLATION_FOREST_ANOMALY", "NUMERICAL_OUTLIERS"]:
                recommendations.append({
                    "id": f"REC-{rec_counter:03d}",
                    "category": "ML_ANOMALY",
                    "priority": "P1_HIGH",
                    "title": f"Quarantine Statistical Outliers & Calibrate Bounds for '{col}'",
                    "finding_ref": ftype,
                    "target_column": col,
                    "rationale": "Multivariate / numerical boundary violation detected. May indicate currency unit confusion, decimal placement error, or sensor failure.",
                    "action_type": "OUTLIER_QUARANTINE",
                    "suggested_fix": (
                        f"-- Divert outliers into dead-letter queue for manual data steward review\n"
                        f"INSERT INTO dlq_anomalous_records\n"
                        f"SELECT * FROM current_dataset WHERE is_anomalous = TRUE;"
                    ),
                    "impact": "Isolates corrupted metrics while allowing clean batch records to proceed.",
                })
                rec_counter += 1

        # Priority sorting: P0 -> P1 -> P2 -> P3
        priority_weights = {"P0_CRITICAL": 0, "P1_HIGH": 1, "P2_MEDIUM": 2, "P3_LOW": 3}
        recommendations.sort(key=lambda r: priority_weights.get(r["priority"], 9))

        return {
            "agent": self.name,
            "status": "RECOMMENDATIONS_READY",
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "summary": (
                f"Generated {len(recommendations)} actionable recommendation(s) "
                f"ranked by severity to mitigate observed data pipeline risks."
            ),
        }
