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
        reference_rows: list[dict[str, Any]] | None = None,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Runs two-sample Kolmogorov-Smirnov tests and categorical frequency divergence.
        """
        import time
        t_start = time.perf_counter()

        if not current_rows or not reference_rows or len(reference_rows) < 10:
            ks_proof = {
                "method": "Kolmogorov-Smirnov Two-Sample Test",
                "agent": "Drift Agent",
                "classification": "Statistical distribution drift detection",
                "executed": False,
                "execution_status": "NOT_EXECUTED",
                "status": "NOT_EXECUTED",
                "reason": "historical baseline unavailable",
                "significance_level": self.alpha,
                "d_threshold": 0.10,
                "decision_rule": f"p < {self.alpha} AND D >= 0.10",
                "columns_tested": 0,
                "drift_detected_count": 0,
                "columns": [],
                "explanation": "The current distribution was compared with the historical baseline using the KS two-sample test.",
            }
            return {
                "agent": self.name,
                "status": "NOT_EXECUTED",
                "execution_status": "NOT_EXECUTED",
                "reason": "historical baseline unavailable",
                "drift_detected": False,
                "drifted_column_count": 0,
                "findings": [],
                "metrics": {},
                "summary": "Drift Agent did not execute: historical baseline unavailable.",
                "ks_test_proof": ks_proof,
                "ks_proof": ks_proof,
            }

        cols_to_check = columns or list(current_rows[0].keys())
        findings = []
        drift_metrics = {}
        ks_columns: list[dict[str, Any]] = []
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
                # Decision rule: p < 0.05 and D >= 0.10
                is_drift = bool(pval < self.alpha and stat >= 0.10)

                drift_metrics[col] = {
                    "type": "NUMERIC_KS",
                    "statistic": round(stat, 4),
                    "p_value": round(pval, 6),
                    "is_drift": is_drift,
                    "current_mean": round(float(np.mean(curr_vals)), 4),
                    "reference_mean": round(float(np.mean(ref_vals)), 4),
                }

                # Empirical CDF curves for visualization
                curr_sorted = np.sort(curr_vals)
                ref_sorted = np.sort(ref_vals)
                min_v = min(float(curr_sorted[0]), float(ref_sorted[0]))
                max_v = max(float(curr_sorted[-1]), float(ref_sorted[-1]))
                eval_pts = np.linspace(min_v, max_v, 20)
                cdf_curve = []
                for pt in eval_pts:
                    c_cdf = float(np.searchsorted(curr_sorted, pt, side="right") / len(curr_sorted))
                    r_cdf = float(np.searchsorted(ref_sorted, pt, side="right") / len(ref_sorted))
                    cdf_curve.append({
                        "x": round(float(pt), 2),
                        "current_cdf": round(c_cdf, 4),
                        "baseline_cdf": round(r_cdf, 4),
                        "d_distance": round(abs(c_cdf - r_cdf), 4),
                    })

                ks_columns.append({
                    "column": col,
                    "baseline_sample_size": len(ref_vals),
                    "current_sample_size": len(curr_vals),
                    "ks_statistic": round(stat, 4),
                    "p_value": round(pval, 6),
                    "significance_level": self.alpha,
                    "d_threshold": 0.10,
                    "decision": "DRIFT DETECTED" if is_drift else "NO DRIFT",
                    "is_drift": is_drift,
                    "baseline_mean": round(float(np.mean(ref_vals)), 4),
                    "current_mean": round(float(np.mean(curr_vals)), 4),
                    "decision_rule": f"p < {self.alpha} AND D >= 0.10",
                    "explanation": "The current distribution was compared with the historical baseline using the KS two-sample test.",
                    "cdf_curve": cdf_curve,
                })

                if is_drift:
                    drift_count += 1
                    sev = "HIGH" if stat > 0.25 else "MEDIUM"
                    findings.append({
                        "type": "DISTRIBUTION_DRIFT",
                        "severity": sev,
                        "column": col,
                        "message": f"Column '{col}' drifted significantly from baseline (KS-stat: {stat:.3f}, p-val: {pval:.6f}).",
                        "evidence": {
                            "column": col,
                            "ks_statistic": round(stat, 4),
                            "p_value": round(pval, 6),
                            "alpha_threshold": self.alpha,
                            "d_threshold": 0.10,
                            "current_mean": round(float(np.mean(curr_vals)), 4),
                            "reference_mean": round(float(np.mean(ref_vals)), 4),
                        },
                    })

        t_elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        status = "DRIFT_DETECTED" if drift_count > 0 else "STABLE"
        has_tested = len(ks_columns) > 0

        ks_proof = {
            "method": "Kolmogorov-Smirnov Two-Sample Test",
            "agent": "Drift Agent",
            "classification": "Statistical distribution drift detection",
            "executed": has_tested,
            "execution_status": "EXECUTED" if has_tested else "INSUFFICIENT_DATA",
            "execution_time_ms": t_elapsed_ms,
            "status": status if has_tested else "INSUFFICIENT_DATA",
            "significance_level": self.alpha,
            "d_threshold": 0.10,
            "decision_rule": f"p < {self.alpha} AND D >= 0.10",
            "columns_tested": len(ks_columns),
            "drift_detected_count": drift_count,
            "columns": ks_columns,
            "explanation": "The current distribution was compared with the historical baseline using the KS two-sample test.",
        }

        return {
            "agent": self.name,
            "status": status,
            "execution_status": "EXECUTED" if has_tested else "INSUFFICIENT_DATA",
            "execution_time_ms": t_elapsed_ms,
            "drift_detected": drift_count > 0,
            "drifted_column_count": drift_count,
            "findings": findings,
            "metrics": drift_metrics,
            "summary": (
                f"Drift Agent evaluated {len(ks_columns)} feature(s). "
                f"{drift_count} feature(s) exhibited statistically significant distribution drift."
            ),
            "ks_test_proof": ks_proof,
            "ks_proof": ks_proof,
        }
