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
        contamination: float = 0.05,
        n_estimators: int = 100,
        random_state: int = 42,
    ) -> None:
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state

    def detect(
        self,
        rows: list[dict[str, Any]],
        numeric_columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Fits IsolationForest on numeric features and detects multivariate anomalies.
        """
        if not rows:
            return {
                "detected": False,
                "anomalous_row_count": 0,
                "anomalous_row_indices": [],
                "anomaly_scores": [],
                "findings": [],
            }

        # 1. Discover all candidate numeric columns
        candidate_cols = numeric_columns or list(rows[0].keys())
        valid_numeric_cols: list[str] = []

        for col in candidate_cols:
            num_count = 0
            for r in rows:
                v = r.get(col)
                if v is not None and str(v).strip() != "":
                    try:
                        fv = float(v)
                        if not (np.isnan(fv) or np.isinf(fv)):
                            num_count += 1
                    except (ValueError, TypeError):
                        pass
            # Consider column numeric if >= 70% of rows parse to float
            if num_count >= (len(rows) * 0.7) and num_count >= 5:
                valid_numeric_cols.append(col)

        if not valid_numeric_cols:
            return {
                "detected": False,
                "message": "No numeric columns available for Isolation Forest",
                "anomalous_row_count": 0,
                "anomalous_row_indices": [],
                "findings": [],
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

        # 3. Fit Isolation Forest
        model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
        )
        # Predictions: -1 for outlier, 1 for inlier
        predictions = model.fit_predict(data_matrix)
        # Decision function: negative values indicate anomalies
        scores = model.decision_function(data_matrix)

        anom_indices = [int(i) for i, p in enumerate(predictions) if p == -1]
        anom_count = len(anom_indices)
        anom_pct = round((anom_count / n_rows) * 100, 2)

        findings = []
        if anom_count > 0:
            severity = "CRITICAL" if anom_pct > 15.0 else ("HIGH" if anom_pct > 5.0 else "MEDIUM")
            findings.append({
                "type": "ML_ISOLATION_FOREST_ANOMALY",
                "severity": severity,
                "message": (
                    f"Isolation Forest identified {anom_count} multivariate anomalous record(s) "
                    f"({anom_pct}% of total) across features: {', '.join(valid_numeric_cols)}."
                ),
                "evidence": {
                    "model": "IsolationForest",
                    "contamination_parameter": self.contamination,
                    "features_analyzed": valid_numeric_cols,
                    "anomalous_row_count": anom_count,
                    "total_rows": n_rows,
                    "anomalous_percentage": anom_pct,
                    "sample_anomalous_indices": anom_indices[:10],
                    "min_decision_score": round(float(np.min(scores)), 4),
                    "mean_decision_score": round(float(np.mean(scores)), 4),
                },
            })

        return {
            "detected": anom_count > 0,
            "features_analyzed": valid_numeric_cols,
            "anomalous_row_count": anom_count,
            "anomalous_percentage": anom_pct,
            "anomalous_row_indices": anom_indices,
            "findings": findings,
            "summary": {
                "total_rows": n_rows,
                "inlier_count": n_rows - anom_count,
                "outlier_count": anom_count,
                "features_count": n_cols,
            },
        }
