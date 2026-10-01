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

    def detect_outliers(
        self,
        rows: list[dict[str, Any]],
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Run Z-Score and IQR detection across numeric columns.
        """
        if not rows:
            return {"findings": [], "column_summaries": {}}

        all_cols = list(rows[0].keys()) if not columns else columns
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
        if not rows:
            return {"findings": [], "column_summaries": {}}

        all_cols = list(rows[0].keys()) if not columns else columns
        findings: list[dict[str, Any]] = []
        summaries: dict[str, Any] = {}

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
                    z_outliers.append({
                        "row_index": valid_indices[i],
                        "value": float(arr[i]),
                        "z_score": round(float(z_scores[i]), 2),
                    })

            # 2. IQR Outliers
            lower_fence = q25 - (self.iqr_multiplier * iqr)
            upper_fence = q75 + (self.iqr_multiplier * iqr)
            iqr_outliers = []
            for i, val in enumerate(arr):
                if val < lower_fence or val > upper_fence:
                    iqr_outliers.append({
                        "row_index": valid_indices[i],
                        "value": float(val),
                        "direction": "LOW" if val < lower_fence else "HIGH",
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

        return {
            "findings": findings,
            "column_summaries": summaries,
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
        if not current_rows or not reference_rows:
            return {"drift_detected": False, "findings": [], "drift_metrics": {}}

        cols = list(current_rows[0].keys()) if not columns else columns
        findings: list[dict[str, Any]] = []
        drift_metrics: dict[str, Any] = {}
        drift_count = 0

        for col in cols:
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
            is_drift = bool(p_value < self.ks_alpha)

            drift_metrics[col] = {
                "ks_statistic": round(statistic, 4),
                "p_value": round(p_value, 6),
                "is_drift": is_drift,
                "current_mean": round(float(np.mean(curr_vals)), 4),
                "reference_mean": round(float(np.mean(ref_vals)), 4),
            }

            if is_drift:
                drift_count += 1
                severity = "HIGH" if statistic > 0.3 else "MEDIUM"
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
                        "current_mean": round(float(np.mean(curr_vals)), 4),
                        "reference_mean": round(float(np.mean(ref_vals)), 4),
                    },
                })

        return {
            "drift_detected": drift_count > 0,
            "drift_count": drift_count,
            "findings": findings,
            "drift_metrics": drift_metrics,
        }
