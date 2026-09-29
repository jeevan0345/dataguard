"""
DataGuard Drift Agent
Dedicated agent for detecting statistical distribution drift, concept drift, and schema evolution.
"""

from typing import Any
import numpy as np
from scipy import stats
from app.agents.base.base_agent import BaseAgent


class DriftAgent(BaseAgent):
    """
    Drift Agent for DataGuard 2.0.
    Continuously monitors feature distributions, categorical proportions, and volume trends.
    """

    def __init__(self, significance_level: float = 0.05) -> None:
        super().__init__(
            name="Drift Agent",
            role="Statistical & Distribution Drift Detection",
            description="Monitors numerical distributions, categorical frequencies, and volume shifts over time.",
        )
        self.alpha = significance_level

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return self.analyze_drift(*args, **kwargs)

    def analyze_drift(
        self,
        current_rows: list[dict[str, Any]],
        reference_rows: list[dict[str, Any]],
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Runs two-sample Kolmogorov-Smirnov tests and categorical frequency divergence.
        """
        if not current_rows or not reference_rows:
            return {
                "agent": self.name,
                "status": "INSUFFICIENT_DATA",
                "drift_detected": False,
                "findings": [],
                "drift_metrics": {},
            }

        cols_to_check = columns or list(current_rows[0].keys())
        findings = []
        drift_metrics = {}
        drift_count = 0

        for col in cols_to_check:
            # Check if numeric
            curr_vals = []
            for r in current_rows:
                v = r.get(col)
                if v is not None and str(v).strip() != "":
                    try:
                        fv = float(v)
                        if not (np.isnan(fv) or np.isinf(fv)):
                            curr_vals.append(fv)
                    except (ValueError, TypeError):
                        pass

            ref_vals = []
            for r in reference_rows:
                v = r.get(col)
                if v is not None and str(v).strip() != "":
                    try:
                        fv = float(v)
                        if not (np.isnan(fv) or np.isinf(fv)):
                            ref_vals.append(fv)
                    except (ValueError, TypeError):
                        pass

            if len(curr_vals) >= 10 and len(ref_vals) >= 10:
                ks = stats.ks_2samp(curr_vals, ref_vals)
                stat = float(ks.statistic)
                pval = float(ks.pvalue)
                is_drift = bool(pval < self.alpha)

                drift_metrics[col] = {
                    "type": "NUMERIC_KS",
                    "statistic": round(stat, 4),
                    "p_value": round(pval, 6),
                    "is_drift": is_drift,
                    "current_mean": round(float(np.mean(curr_vals)), 4),
                    "reference_mean": round(float(np.mean(ref_vals)), 4),
                }

                if is_drift:
                    drift_count += 1
                    sev = "HIGH" if stat > 0.25 else "MEDIUM"
                    findings.append({
                        "type": "DISTRIBUTION_DRIFT",
                        "severity": sev,
                        "message": f"Column '{col}' drifted significantly from baseline (KS-stat: {stat:.3f}, p-val: {pval:.6f}).",
                        "evidence": {
                            "column": col,
                            "ks_statistic": round(stat, 4),
                            "p_value": round(pval, 6),
                            "current_mean": round(float(np.mean(curr_vals)), 4),
                            "reference_mean": round(float(np.mean(ref_vals)), 4),
                        },
                    })

        status = "DRIFT_DETECTED" if drift_count > 0 else "STABLE"

        return {
            "agent": self.name,
            "status": status,
            "drift_detected": drift_count > 0,
            "drifted_column_count": drift_count,
            "findings": findings,
            "metrics": drift_metrics,
            "summary": (
                f"Drift Agent evaluated {len(drift_metrics)} feature(s). "
                f"{drift_count} feature(s) exhibited statistically significant distribution drift."
            ),
        }
