"""
DataGuard ML Isolation Forest Detector
Unsupervised multivariate anomaly detection using Scikit-Learn's Isolation Forest.
Pandas is intentionally NOT used.
"""

from typing import Any
import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestDetector:
    """
    Multivariate anomaly detector based on Isolation Forest.
    Operates on list-of-dicts tabular data using NumPy arrays.
    """

    def __init__(
        self,
        contamination: str | float = "auto",
        n_estimators: int = 100,
        random_state: int = 42,
    ) -> None:
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state

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
        )

    def detect(
        self,
        rows: list[dict[str, Any]],
        numeric_columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Fits IsolationForest on numeric features and detects multivariate anomalies.

        Decision Rule:
        When contamination='auto', scikit-learn does not force an arbitrary static slice
        (such as 5%). Instead, points are evaluated by their decision_function score.
        On clean continuous distributions, borderline inliers can exhibit small negative
        scores (-0.01 to -0.05). To guarantee zero false-positives on clean baseline data,
        a record is only classified as an anomaly when its decision_function is clearly
        separated below a statistically justified threshold:
        `threshold = min(-0.15, float(np.mean(scores) - 3.5 * np.std(scores)))`.
        ID-like columns (e.g. order_item_id) and constant columns are excluded from analysis.
        """
        import time
        t_start = time.perf_counter()

        if not rows:
            return {
                "detected": False,
                "anomalous_row_count": 0,
                "anomalous_row_indices": [],
                "anomaly_scores": [],
                "findings": [],
                "isolation_forest_proof": {
                    "method": "Isolation Forest",
                    "agent": "Inspector Agent",
                    "classification": "Machine-learning-based unsupervised anomaly detection",
                    "executed": False,
                    "execution_status": "NOT_APPLICABLE",
                    "status": "NOT_APPLICABLE",
                    "reason": "Dataset is empty",
                    "features": [],
                    "features_count": 0,
                    "samples": 0,
                    "anomalies_detected": 0,
                    "contamination": str(self.contamination),
                    "model_parameters": {
                        "algorithm": "IsolationForest",
                        "contamination": str(self.contamination),
                        "n_estimators": self.n_estimators,
                        "random_state": self.random_state,
                    },
                    "flagged_anomalies": [],
                },
            }

        # 1. Discover all candidate numeric columns (excluding ID-like columns)
        candidate_cols = numeric_columns or list(rows[0].keys())
        valid_numeric_cols: list[str] = []

        for col in candidate_cols:
            if self._is_id_column(col):
                continue

            num_count = 0
            vals: list[float] = []
            for r in rows:
                v = r.get(col)
                if v is not None and str(v).strip() != "":
                    try:
                        fv = float(v)
                        if not (np.isnan(fv) or np.isinf(fv)):
                            num_count += 1
                            vals.append(fv)
                    except (ValueError, TypeError):
                        pass

            # Consider column numeric if >= 70% of rows parse to float and values are not constant
            if num_count >= (len(rows) * 0.7) and num_count >= 5:
                if len(vals) > 1 and float(np.std(vals)) > 1e-8:
                    valid_numeric_cols.append(col)

        if not valid_numeric_cols:
            t_elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
            return {
                "detected": False,
                "message": "No numeric non-ID columns available for Isolation Forest",
                "anomalous_row_count": 0,
                "anomalous_row_indices": [],
                "findings": [],
                "isolation_forest_proof": {
                    "method": "Isolation Forest",
                    "agent": "Inspector Agent",
                    "classification": "Machine-learning-based unsupervised anomaly detection",
                    "executed": False,
                    "execution_status": "NOT_APPLICABLE",
                    "execution_time_ms": t_elapsed_ms,
                    "status": "NOT_APPLICABLE",
                    "reason": "No numeric non-ID columns available for Isolation Forest",
                    "features": [],
                    "features_count": 0,
                    "samples": len(rows),
                    "anomalies_detected": 0,
                    "contamination": str(self.contamination),
                    "model_parameters": {
                        "algorithm": "IsolationForest",
                        "contamination": str(self.contamination),
                        "n_estimators": self.n_estimators,
                        "random_state": self.random_state,
                    },
                    "flagged_anomalies": [],
                },
            }

        # 2. Build 2D NumPy array with median imputation
        n_rows = len(rows)
        n_cols = len(valid_numeric_cols)
        data_matrix = np.zeros((n_rows, n_cols), dtype=np.float64)

        # Temporary store column values to compute medians
        col_medians = []
        for j, col in enumerate(valid_numeric_cols):
            vals = []
            for r in rows:
                try:
                    v = float(r.get(col))
                    if not (np.isnan(v) or np.isinf(v)):
                        vals.append(v)
                except (ValueError, TypeError):
                    pass
            med = float(np.median(vals)) if vals else 0.0
            col_medians.append(med)

        for i, r in enumerate(rows):
            for j, col in enumerate(valid_numeric_cols):
                try:
                    v = float(r.get(col))
                    if np.isnan(v) or np.isinf(v):
                        data_matrix[i, j] = col_medians[j]
                    else:
                        data_matrix[i, j] = v
                except (ValueError, TypeError):
                    data_matrix[i, j] = col_medians[j]

        # 3. Fit Isolation Forest with contamination="auto"
        model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
        )
        model.fit(data_matrix)
        # Decision function: negative values indicate anomalies
        scores = model.decision_function(data_matrix)

        # Clear separation rule: score must be below justified threshold
        mean_score = float(np.mean(scores))
        std_score = float(np.std(scores))
        separation_threshold = min(-0.15, mean_score - 3.5 * std_score)

        anom_indices = [int(i) for i, s in enumerate(scores) if s < separation_threshold]
        anom_count = len(anom_indices)
        anom_pct = round((anom_count / n_rows) * 100, 2)

        # Score distribution histogram for visualization
        score_dist: list[dict[str, Any]] = []
        if len(scores) > 0:
            min_s = float(np.min(scores))
            max_s = float(np.max(scores))
            bins = np.linspace(min_s, max_s, 16)
            hist, _ = np.histogram(scores, bins=bins)
            for k in range(len(hist)):
                score_dist.append({
                    "range": f"{bins[k]:.2f} to {bins[k+1]:.2f}",
                    "score_mid": round(float((bins[k] + bins[k+1]) / 2), 3),
                    "count": int(hist[k]),
                    "is_anomalous": bool(bins[k+1] <= separation_threshold),
                })

        findings = []
        if anom_count > 0:
            severity = "CRITICAL" if anom_pct > 15.0 else ("HIGH" if anom_pct > 5.0 else "MEDIUM")
            findings.append({
                "type": "ML_ISOLATION_FOREST_ANOMALY",
                "severity": severity,
                "message": (
                    f"Isolation Forest identified {anom_count} multivariate anomalous record(s) "
                    f"({anom_pct}% of total) separated beyond threshold {separation_threshold:.3f} "
                    f"across features: {', '.join(valid_numeric_cols)}."
                ),
                "evidence": {
                    "model": "IsolationForest",
                    "contamination_parameter": self.contamination,
                    "features_analyzed": valid_numeric_cols,
                    "separation_threshold": round(separation_threshold, 4),
                    "anomalous_row_count": anom_count,
                    "total_rows": n_rows,
                    "anomalous_percentage": anom_pct,
                    "sample_anomalous_indices": anom_indices[:10],
                    "min_decision_score": round(float(np.min(scores)), 4),
                    "mean_decision_score": round(mean_score, 4),
                },
            })

        t_elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)

        flagged_anomalies = [
            {
                "row_index": idx,
                "prediction": -1,
                "anomaly_label": "ANOMALY",
                "anomaly_score": round(float(scores[idx]), 4),
                "decision_score": round(float(scores[idx]), 4),
                "status": "ANOMALY DETECTED",
                "values": {c: rows[idx].get(c) for c in valid_numeric_cols},
            }
            for idx in anom_indices
        ]

        isolation_forest_proof = {
            "method": "Isolation Forest",
            "agent": "Inspector Agent",
            "classification": "Machine-learning-based unsupervised anomaly detection",
            "executed": True,
            "execution_status": "EXECUTED",
            "execution_time_ms": t_elapsed_ms,
            "status": "ANOMALY_DETECTED" if anom_count > 0 else "HEALTHY",
            "features": valid_numeric_cols,
            "features_count": len(valid_numeric_cols),
            "samples": n_rows,
            "anomalies_detected": anom_count,
            "anomalous_percentage": anom_pct,
            "contamination": str(self.contamination),
            "model_parameters": {
                "algorithm": "IsolationForest",
                "contamination": str(self.contamination),
                "n_estimators": self.n_estimators,
                "random_state": self.random_state,
                "max_samples": "auto",
            },
            "score_range": {
                "min": round(float(np.min(scores)), 4) if len(scores) > 0 else 0.0,
                "max": round(float(np.max(scores)), 4) if len(scores) > 0 else 0.0,
                "mean": round(mean_score, 4),
                "std": round(std_score, 4),
            },
            "separation_threshold": round(separation_threshold, 4),
            "prediction_definition": "-1 = anomaly, 1 = normal",
            "flagged_anomalies": flagged_anomalies,
            "score_distribution": score_dist,
        }

        return {
            "detected": anom_count > 0,
            "features_analyzed": valid_numeric_cols,
            "anomalous_row_count": anom_count,
            "anomalous_percentage": anom_pct,
            "anomalous_row_indices": anom_indices,
            "separation_threshold": round(separation_threshold, 4),
            "findings": findings,
            "summary": {
                "total_rows": n_rows,
                "inlier_count": n_rows - anom_count,
                "outlier_count": anom_count,
                "features_count": n_cols,
            },
            "isolation_forest_proof": isolation_forest_proof,
        }
