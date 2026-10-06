"""
DataGuard Unified ML Anomaly Engine
Coordinates Statistical Profiling, Z-Score/IQR Outliers, KS Distribution Drift,
and Isolation Forest Multivariate Anomaly Detection.
"""

from typing import Any
from app.ml.profiler import DatasetProfiler
from app.ml.statistical_detector import StatisticalAnomalyDetector
from app.ml.isolation_forest import IsolationForestDetector


class MLEngine:
    """
    Unified Machine Learning & Statistical Anomaly Engine for DataGuard.
    """

    def __init__(
        self,
        z_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
        contamination: str | float = "auto",
    ) -> None:
        self.profiler = DatasetProfiler()
        self.statistical_detector = StatisticalAnomalyDetector(
            z_threshold=z_threshold,
            iqr_multiplier=iqr_multiplier,
        )
        self.isolation_forest = IsolationForestDetector(
            contamination=contamination,
        )

    def analyze(
        self,
        rows: list[dict[str, Any]],
        reference_rows: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Run complete ML analysis:
        1. Statistical Profiling
        2. Univariate Statistical Detection (Z-Score & IQR)
        3. Multivariate ML Anomaly Detection (Isolation Forest)
        Note: Distribution Drift (KS-Test) is owned and executed once by DriftAgent.
        """
        if not rows:
            return {
                "status": "EMPTY_DATASET",
                "findings": [],
                "profiles": {},
                "ml_summary": {},
            }

        # 1. Profile dataset
        profile_res = self.profiler.profile(rows)

        # 2. Statistical Outliers
        stat_res = self.statistical_detector.detect_outliers(rows)

        # 3. Distribution Drift metrics (KS drift findings are owned solely by DriftAgent)
        drift_res: dict[str, Any] = {"drift_detected": False, "findings": []}
        if reference_rows and len(reference_rows) >= 10:
            drift_res = self.statistical_detector.detect_distribution_drift(
                current_rows=rows,
                reference_rows=reference_rows,
            )

        # 4. Multivariate Isolation Forest
        if_res = self.isolation_forest.detect(rows)

        # 5. Collect ML findings (Univariate Outliers + Multivariate Isolation Forest; DriftAgent owns drift)
        all_findings: list[dict[str, Any]] = []
        all_findings.extend(stat_res.get("findings", []))
        all_findings.extend(if_res.get("findings", []))

        status = "ANOMALY_DETECTED" if all_findings else "HEALTHY"

        return {
            "engine": "DataGuard ML Engine",
            "status": status,
            "row_count": len(rows),
            "finding_count": len(all_findings),
            "findings": all_findings,
            "profile": profile_res,
            "statistical_summary": stat_res.get("column_summaries", {}),
            "distribution_drift": drift_res,
            "isolation_forest": if_res.get("summary", {}),
            "ml_proof": {
                "z_score": stat_res.get("z_score_proof", {}),
                "iqr": stat_res.get("iqr_proof", {}),
                "isolation_forest": if_res.get("isolation_forest_proof", {}),
                "ks_test": drift_res.get("ks_test_proof", {}),
            },
        }
