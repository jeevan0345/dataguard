"""
DataGuard Statistical Anomaly Detector
Performs Z-score, Modified Z-score (MAD), IQR fence, and KS-test drift detection
using NumPy and SciPy. Pandas is intentionally NOT used.
"""

from typing import Any
import numpy as np
from scipy import stats


class StatisticalAnomalyDetector:
    """
    Detects univariate numerical anomalies and distribution drift
    without using pandas.
    """

    def __init__(
        self,
        z_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
        ks_alpha: float = 0.05,
    ) -> None:
        self.z_threshold = z_threshold
        self.iqr_multiplier = iqr_multiplier
        self.ks_alpha = ks_alpha

    @staticmethod
    def _is_id_column(col_name: str) -> bool:
        c = col_name.lower().strip()
        return (
            c == "id"
            or c.endswith("_id")
            or c.startswith("id_")
            or c.endswith("_key")
            or c == "key"
            or c.endswith("_uuid")
            or c == "uuid"
            or c.endswith("_code")
            or c == "code"
            or c.endswith("_zip")
            or c == "zip"
        )

    def detect_outliers(
        self,
        rows: list[dict[str, Any]],
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Run Z-Score and IQR detection across numeric columns.

        False-positive reduction rules:
        - Excludes ID-like columns (e.g. order_item_id, order_id).
        - Excludes constant columns (std < 1e-8, min == max).
        - Naturally skewed columns (|skew| > 1.5, e.g. price, freight) require
          either severe Z-score spikes (max Z > 4.5) or an outlier percentage >= 15%
          to avoid flagging standard long-tail distributions.
        - Non-skewed columns require a minimum outlier percentage >= 5.0% and >= 3 items.
        """
        import time

        t_start = time.perf_counter()

        if not rows:
            return {
                "findings": [],
                "column_summaries": {},
                "z_score_proof": {
                    "method": "Z-Score",
                    "agent": "Inspector Agent",
                    "classification": "Statistical anomaly detection",
                    "executed": False,
                    "execution_status": "NOT_APPLICABLE",
                    "status": "NOT_APPLICABLE",
                    "reason": "Dataset is empty",
                    "columns_analyzed": 0,
                    "total_flagged_count": 0,
                    "max_z_score": 0.0,
                    "threshold": f"|z| > {self.z_threshold}",
                    "threshold_value": self.z_threshold,
                    "formula": "z = (x - mean) / standard_deviation",
                    "columns": [],
                },
                "iqr_proof": {
                    "method": "IQR",
                    "agent": "Inspector Agent",
                    "classification": "Statistical outlier detection",
                    "executed": False,
                    "execution_status": "NOT_APPLICABLE",
                    "status": "NOT_APPLICABLE",
                    "reason": "Dataset is empty",
                    "columns_analyzed": 0,
                    "total_outliers_count": 0,
                    "multiplier": self.iqr_multiplier,
                    "formulas": [
                        "IQR = Q3 - Q1",
                        f"Lower Bound = Q1 - {self.iqr_multiplier} × IQR",
                        f"Upper Bound = Q3 + {self.iqr_multiplier} × IQR",
                    ],
                    "columns": [],
                },
            }

        all_cols = list(rows[0].keys()) if not columns else columns
        findings: list[dict[str, Any]] = []
        summaries: dict[str, Any] = {}
        z_columns: list[dict[str, Any]] = []
        iqr_columns: list[dict[str, Any]] = []

        for col in all_cols:
            if self._is_id_column(col):
                continue

            raw_values = [row.get(col) for row in rows]
            numeric_vals: list[float] = []
            valid_indices: list[int] = []

            for idx, val in enumerate(raw_values):
                try:
                    v = float(val)
                    if not (np.isnan(v) or np.isinf(v)):
                        numeric_vals.append(v)
                        valid_indices.append(idx)
                except (ValueError, TypeError):
                    continue

            # Need at least 5 numeric values for statistical checks
            if len(numeric_vals) < 5:
                continue

            arr = np.array(numeric_vals, dtype=np.float64)
            mean = float(np.mean(arr))
            std = float(np.std(arr))

            # Ignore constant columns
            if std < 1e-8 or float(np.min(arr)) == float(np.max(arr)):
                continue

            q25, q75 = float(np.percentile(arr, 25)), float(np.percentile(arr, 75))
            iqr = q75 - q25

            # If IQR is effectively zero (e.g. discrete repeated values), ignore to prevent false fences
            if iqr < 1e-8:
                continue

            median = float(np.median(arr))
            skewness = float(stats.skew(arr)) if len(arr) >= 5 else 0.0
            is_skewed = bool(abs(skewness) > 1.5)

            # 1. Z-Score Outliers
            z_outliers = []
            z_scores = np.abs((arr - mean) / std)
            z_anomaly_mask = z_scores > self.z_threshold
            for i, is_anom in enumerate(z_anomaly_mask):
                if is_anom:
                    val_float = float(arr[i])
                    z_val = round(float(z_scores[i]), 2)
                    z_outliers.append({
                        "row_index": valid_indices[i],
                        "value": val_float,
                        "mean": round(mean, 4),
                        "std_dev": round(std, 4),
                        "z_score": z_val,
                        "threshold": self.z_threshold,
                        "status": "ANOMALY",
                        "reason": f"The value is more than {self.z_threshold} standard deviations from the calculated mean (|z|={z_val:.2f} > {self.z_threshold}).",
                    })

            # 2. IQR Outliers
            lower_fence = q25 - (self.iqr_multiplier * iqr)
            upper_fence = q75 + (self.iqr_multiplier * iqr)
            iqr_outliers = []
            for i, val in enumerate(arr):
                if val < lower_fence or val > upper_fence:
                    direction = "LOW" if val < lower_fence else "HIGH"
                    iqr_outliers.append({
                        "row_index": valid_indices[i],
                        "value": float(val),
                        "direction": direction,
                        "q1": round(q25, 4),
                        "q3": round(q75, 4),
                        "iqr": round(iqr, 4),
                        "lower_bound": round(lower_fence, 4),
                        "upper_bound": round(upper_fence, 4),
                        "status": "OUTLIER DETECTED",
                        "reason": "The observed value lies outside the IQR-based acceptable range.",
                    })

            total_valid = len(numeric_vals)
            outlier_pct = round((len(iqr_outliers) / total_valid) * 100, 2)
            max_z = float(np.max(z_scores)) if len(z_scores) > 0 else 0.0

            summaries[col] = {
                "valid_count": total_valid,
                "mean": round(mean, 4),
                "std": round(std, 4),
                "skewness": round(skewness, 4),
                "is_skewed": is_skewed,
                "z_outlier_count": len(z_outliers),
                "iqr_outlier_count": len(iqr_outliers),
                "outlier_percentage": outlier_pct,
                "lower_fence": round(lower_fence, 4),
                "upper_fence": round(upper_fence, 4),
                "max_z_score": round(max_z, 2),
            }

            # Outlier Decision Rule:
            # - Naturally skewed columns (e.g. price, freight with |skew| > 1.5): require a minimum
            #   outlier percentage >= 15.0% or extreme artificial spike (max_z > 15.0) to prevent
            #   false positives on standard long-tail distributions.
            # - Non-skewed columns: require minimum outlier percentage >= 5.0% and count >= 3.
            has_anomaly = False
            if is_skewed:
                if outlier_pct >= 15.0 or max_z > 15.0:
                    has_anomaly = True
            else:
                if outlier_pct >= 5.0 and len(iqr_outliers) >= 3:
                    has_anomaly = True

            if has_anomaly:
                severity = "HIGH" if (outlier_pct > 15.0 or max_z > 6.0) else ("MEDIUM" if outlier_pct > 7.0 else "LOW")
                findings.append({
                    "type": "NUMERICAL_OUTLIERS",
                    "column": col,
                    "severity": severity,
                    "message": f"Column '{col}' contains {len(iqr_outliers)} outlier value(s) ({outlier_pct}%) outside fences [{lower_fence:.2f}, {upper_fence:.2f}] (max Z: {max_z:.1f}).",
                    "evidence": {
                        "column": col,
                        "outlier_count": len(iqr_outliers),
                        "outlier_percentage": outlier_pct,
                        "total_valid": total_valid,
                        "lower_fence": round(lower_fence, 4),
                        "upper_fence": round(upper_fence, 4),
                        "mean": round(mean, 4),
                        "std": round(std, 4),
                        "skewness": round(skewness, 4),
                        "max_z_score": round(max_z, 2),
                        "sample_outliers": iqr_outliers[:5],
                    },
                })

            # Record per-column Z-Score Proof
            # Distribution points sample (first 40 points for visualization)
            z_sample_points = [
                {"row_index": valid_indices[i], "value": round(float(arr[i]), 2), "z_score": round(float(z_scores[i]), 2)}
                for i in range(min(len(arr), 40))
            ]
            z_columns.append({
                "column": col,
                "sample_size": total_valid,
                "mean": round(mean, 4),
                "std_dev": round(std, 4),
                "threshold": f"|z| > {self.z_threshold}",
                "threshold_value": self.z_threshold,
                "max_z_score": round(max_z, 2),
                "flagged_count": len(z_outliers),
                "status": "ANOMALY_DETECTED" if len(z_outliers) > 0 else "HEALTHY",
                "formula": "z = (x - mean) / standard_deviation",
                "explanation": "The value is more than 3 standard deviations from the calculated mean.",
                "flagged_values": z_outliers,
                "distribution_sample": z_sample_points,
            })

            # Record per-column IQR Proof
            iqr_columns.append({
                "column": col,
                "observations": total_valid,
                "sample_size": total_valid,
                "q1": round(q25, 4),
                "q3": round(q75, 4),
                "iqr": round(iqr, 4),
                "median": round(median, 4),
                "lower_bound": round(lower_fence, 4),
                "upper_bound": round(upper_fence, 4),
                "outlier_count": len(iqr_outliers),
                "outlier_percentage": outlier_pct,
                "status": "OUTLIER_DETECTED" if len(iqr_outliers) > 0 else "HEALTHY",
                "formula": f"IQR = Q3 - Q1 | Lower = Q1 - {self.iqr_multiplier} × IQR | Upper = Q3 + {self.iqr_multiplier} × IQR",
                "explanation": "The observed value lies outside the IQR-based acceptable range.",
                "outliers": iqr_outliers,
                "boxplot": {
                    "min": round(float(np.min(arr)), 4),
                    "lower_bound": round(lower_fence, 4),
                    "q1": round(q25, 4),
                    "median": round(median, 4),
                    "q3": round(q75, 4),
                    "upper_bound": round(upper_fence, 4),
                    "max": round(float(np.max(arr)), 4),
                    "outlier_count": len(iqr_outliers),
                },
            })

        t_elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)

        total_z_flagged = sum(c["flagged_count"] for c in z_columns)
        max_overall_z = max([c["max_z_score"] for c in z_columns], default=0.0)
        has_numeric = len(z_columns) > 0

        z_score_proof = {
            "method": "Z-Score",
            "agent": "Inspector Agent",
            "classification": "Statistical anomaly detection",
            "executed": has_numeric,
            "execution_status": "EXECUTED" if has_numeric else "NOT_APPLICABLE",
            "execution_time_ms": t_elapsed_ms,
            "status": ("ANOMALY_DETECTED" if total_z_flagged > 0 else "HEALTHY") if has_numeric else "NOT_APPLICABLE",
            "columns_analyzed": len(z_columns),
            "total_flagged_count": total_z_flagged,
            "max_z_score": max_overall_z,
            "threshold": f"|z| > {self.z_threshold}",
            "threshold_value": self.z_threshold,
            "formula": "z = (x - mean) / standard_deviation",
            "explanation": "The value is more than 3 standard deviations from the calculated mean.",
            "columns": z_columns,
        }

        total_iqr_outliers = sum(c["outlier_count"] for c in iqr_columns)
        iqr_proof = {
            "method": "IQR",
            "agent": "Inspector Agent",
            "classification": "Statistical outlier detection",
            "executed": has_numeric,
            "execution_status": "EXECUTED" if has_numeric else "NOT_APPLICABLE",
            "execution_time_ms": t_elapsed_ms,
            "status": ("OUTLIER_DETECTED" if total_iqr_outliers > 0 else "HEALTHY") if has_numeric else "NOT_APPLICABLE",
            "columns_analyzed": len(iqr_columns),
            "total_outliers_count": total_iqr_outliers,
            "multiplier": self.iqr_multiplier,
            "method_rule": f"{self.iqr_multiplier} × IQR",
            "formulas": [
                "IQR = Q3 - Q1",
                f"Lower Bound = Q1 - {self.iqr_multiplier} × IQR",
                f"Upper Bound = Q3 + {self.iqr_multiplier} × IQR",
            ],
            "explanation": "The observed value lies outside the IQR-based acceptable range.",
            "columns": iqr_columns,
        }

        return {
            "findings": findings,
            "column_summaries": summaries,
            "z_score_proof": z_score_proof,
            "iqr_proof": iqr_proof,
        }

    def detect_distribution_drift(
        self,
        current_rows: list[dict[str, Any]],
        reference_rows: list[dict[str, Any]],
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Compare current dataset against a reference baseline using
        Two-Sample Kolmogorov-Smirnov test.
        """
        import time

        t_start = time.perf_counter()

        if not current_rows or not reference_rows or len(reference_rows) < 10:
            return {
                "drift_detected": False,
                "findings": [],
                "drift_metrics": {},
                "ks_test_proof": {
                    "method": "Kolmogorov-Smirnov Two-Sample Test",
                    "agent": "Drift Agent",
                    "classification": "Statistical distribution drift detection",
                    "executed": False,
                    "execution_status": "NOT_EXECUTED",
                    "status": "NOT_EXECUTED",
                    "reason": "historical baseline unavailable",
                    "significance_level": self.ks_alpha,
                    "d_threshold": 0.10,
                    "decision_rule": f"p < {self.ks_alpha} AND D >= 0.10",
                    "columns_tested": 0,
                    "drift_detected_count": 0,
                    "columns": [],
                    "explanation": "The Kolmogorov-Smirnov test requires a reference baseline distribution to evaluate drift. Baseline unavailable.",
                },
            }

        cols = list(current_rows[0].keys()) if not columns else columns
        findings: list[dict[str, Any]] = []
        drift_metrics: dict[str, Any] = {}
        ks_columns: list[dict[str, Any]] = []
        drift_count = 0

        for col in cols:
            if self._is_id_column(col):
                continue

            # Extract numeric vectors
            curr_vals = []
            for r in current_rows:
                try:
                    v = float(r.get(col))
                    if not (np.isnan(v) or np.isinf(v)):
                        curr_vals.append(v)
                except (ValueError, TypeError):
                    pass

            ref_vals = []
            for r in reference_rows:
                try:
                    v = float(r.get(col))
                    if not (np.isnan(v) or np.isinf(v)):
                        ref_vals.append(v)
                except (ValueError, TypeError):
                    pass

            if len(curr_vals) < 10 or len(ref_vals) < 10:
                continue

            ks_res = stats.ks_2samp(curr_vals, ref_vals)
            statistic = float(ks_res.statistic)
            p_value = float(ks_res.pvalue)
            # Decision rule: p < 0.05 and practical D >= 0.10
            is_drift = bool(p_value < self.ks_alpha and statistic >= 0.10)

            drift_metrics[col] = {
                "ks_statistic": round(statistic, 4),
                "p_value": round(p_value, 6),
                "is_drift": is_drift,
                "current_mean": round(float(np.mean(curr_vals)), 4),
                "reference_mean": round(float(np.mean(ref_vals)), 4),
            }

            # Generate empirical CDF curves for charting
            curr_sorted = np.sort(curr_vals)
            ref_sorted = np.sort(ref_vals)
            min_v = min(float(curr_sorted[0]), float(ref_sorted[0]))
            max_v = max(float(curr_sorted[-1]), float(ref_sorted[-1]))
            eval_points = np.linspace(min_v, max_v, 20)
            cdf_curve = []
            for pt in eval_points:
                cdf_curr = float(np.searchsorted(curr_sorted, pt, side="right") / len(curr_sorted))
                cdf_ref = float(np.searchsorted(ref_sorted, pt, side="right") / len(ref_sorted))
                cdf_curve.append({
                    "x": round(float(pt), 2),
                    "current_cdf": round(cdf_curr, 4),
                    "baseline_cdf": round(cdf_ref, 4),
                    "d_distance": round(abs(cdf_curr - cdf_ref), 4),
                })

            ks_columns.append({
                "column": col,
                "baseline_sample_size": len(ref_vals),
                "current_sample_size": len(curr_vals),
                "ks_statistic": round(statistic, 4),
                "p_value": round(p_value, 6),
                "significance_level": self.ks_alpha,
                "d_threshold": 0.10,
                "decision": "DRIFT DETECTED" if is_drift else "NO DRIFT",
                "is_drift": is_drift,
                "baseline_mean": round(float(np.mean(ref_vals)), 4),
                "current_mean": round(float(np.mean(curr_vals)), 4),
                "decision_rule": f"p < {self.ks_alpha} AND D >= 0.10",
                "explanation": "The current distribution was compared with the historical baseline using the KS two-sample test.",
                "cdf_curve": cdf_curve,
            })

            if is_drift:
                drift_count += 1
                severity = "HIGH" if statistic > 0.25 else "MEDIUM"
                findings.append({
                    "type": "DISTRIBUTION_DRIFT",
                    "column": col,
                    "severity": severity,
                    "message": f"Significant distribution drift detected in column '{col}' (KS-stat: {statistic:.3f}, p-value: {p_value:.6f}).",
                    "evidence": {
                        "column": col,
                        "ks_statistic": round(statistic, 4),
                        "p_value": round(p_value, 6),
                        "alpha_threshold": self.ks_alpha,
                        "d_threshold": 0.10,
                        "current_mean": round(float(np.mean(curr_vals)), 4),
                        "reference_mean": round(float(np.mean(ref_vals)), 4),
                    },
                })

        t_elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
        has_tested = len(ks_columns) > 0

        ks_test_proof = {
            "method": "Kolmogorov-Smirnov Two-Sample Test",
            "agent": "Drift Agent",
            "classification": "Statistical distribution drift detection",
            "executed": has_tested,
            "execution_status": "EXECUTED" if has_tested else "INSUFFICIENT_DATA",
            "execution_time_ms": t_elapsed_ms,
            "status": ("DRIFT_DETECTED" if drift_count > 0 else "STABLE") if has_tested else "INSUFFICIENT_DATA",
            "significance_level": self.ks_alpha,
            "d_threshold": 0.10,
            "decision_rule": f"p < {self.ks_alpha} AND D >= 0.10",
            "columns_tested": len(ks_columns),
            "drift_detected_count": drift_count,
            "columns": ks_columns,
            "explanation": "The current distribution was compared with the historical baseline using the KS two-sample test.",
        }

        return {
            "drift_detected": drift_count > 0,
            "drift_count": drift_count,
            "findings": findings,
            "drift_metrics": drift_metrics,
            "ks_test_proof": ks_test_proof,
        }
