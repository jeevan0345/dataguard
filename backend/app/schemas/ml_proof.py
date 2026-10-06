from typing import Any, Optional
from pydantic import BaseModel, Field


class ZScoreColumnProof(BaseModel):
    column: str
    sample_size: int
    mean: float
    std_dev: float
    threshold: str
    threshold_value: float = 3.0
    max_z_score: float
    flagged_count: int
    status: str
    formula: str = "z = (x - mean) / standard_deviation"
    explanation: str = "The value is more than 3 standard deviations from the calculated mean."
    flagged_values: list[dict[str, Any]] = []
    distribution_sample: list[dict[str, Any]] = []
    related_finding_id: Optional[str] = None


class ZScoreMethodProof(BaseModel):
    method: str = "Z-Score"
    agent: str = "Inspector Agent"
    classification: str = "Statistical anomaly detection"
    executed: bool
    execution_status: str  # EXECUTED | NOT_APPLICABLE | FAILED
    execution_time_ms: Optional[float] = None
    status: str  # ANOMALY_DETECTED | HEALTHY | NOT_APPLICABLE
    columns_analyzed: int = 0
    total_flagged_count: int = 0
    max_z_score: float = 0.0
    threshold: str = "|z| > 3.0"
    threshold_value: float = 3.0
    formula: str = "z = (x - mean) / standard_deviation"
    explanation: str = "The value is more than 3 standard deviations from the calculated mean."
    columns: list[dict[str, Any]] = []


class IQRColumnProof(BaseModel):
    column: str
    observations: int
    sample_size: int
    q1: float
    q3: float
    iqr: float
    median: float
    lower_bound: float
    upper_bound: float
    outlier_count: int
    outlier_percentage: float
    status: str
    formula: str = "IQR = Q3 - Q1 | Lower = Q1 - 1.5 × IQR | Upper = Q3 + 1.5 × IQR"
    explanation: str = "The observed value lies outside the IQR-based acceptable range."
    outliers: list[dict[str, Any]] = []
    boxplot: Optional[dict[str, Any]] = None
    related_finding_id: Optional[str] = None


class IQRMethodProof(BaseModel):
    method: str = "IQR"
    agent: str = "Inspector Agent"
    classification: str = "Statistical outlier detection"
    executed: bool
    execution_status: str  # EXECUTED | NOT_APPLICABLE | FAILED
    execution_time_ms: Optional[float] = None
    status: str  # OUTLIER_DETECTED | HEALTHY | NOT_APPLICABLE
    columns_analyzed: int = 0
    total_outliers_count: int = 0
    multiplier: float = 1.5
    method_rule: str = "1.5 × IQR"
    formulas: list[str] = [
        "IQR = Q3 - Q1",
        "Lower Bound = Q1 - 1.5 × IQR",
        "Upper Bound = Q3 + 1.5 × IQR",
    ]
    explanation: str = "The observed value lies outside the IQR-based acceptable range."
    columns: list[dict[str, Any]] = []


class IsolationForestMethodProof(BaseModel):
    method: str = "Isolation Forest"
    agent: str = "Inspector Agent"
    classification: str = "Machine-learning-based unsupervised anomaly detection"
    executed: bool
    execution_status: str  # EXECUTED | NOT_APPLICABLE | FAILED
    execution_time_ms: Optional[float] = None
    status: str  # ANOMALY_DETECTED | HEALTHY | NOT_APPLICABLE
    reason: Optional[str] = None
    features: list[str] = []
    features_count: int = 0
    samples: int = 0
    anomalies_detected: int = 0
    anomalous_percentage: Optional[float] = None
    contamination: str = "auto"
    model_parameters: dict[str, Any] = {}
    score_range: Optional[dict[str, Any]] = None
    separation_threshold: Optional[float] = None
    prediction_definition: str = "-1 = anomaly, 1 = normal"
    flagged_anomalies: list[dict[str, Any]] = []
    score_distribution: list[dict[str, Any]] = []
    related_finding_id: Optional[str] = None


class KSTestColumnProof(BaseModel):
    column: str
    baseline_sample_size: int
    current_sample_size: int
    ks_statistic: float
    p_value: float
    significance_level: float = 0.05
    d_threshold: float = 0.10
    decision: str  # DRIFT DETECTED | NO DRIFT
    is_drift: bool
    baseline_mean: float
    current_mean: float
    decision_rule: str = "p < 0.05 AND D >= 0.10"
    explanation: str = "The current distribution was compared with the historical baseline using the KS two-sample test."
    cdf_curve: list[dict[str, Any]] = []
    related_finding_id: Optional[str] = None


class KSTestMethodProof(BaseModel):
    method: str = "Kolmogorov-Smirnov Two-Sample Test"
    agent: str = "Drift Agent"
    classification: str = "Statistical distribution drift detection"
    executed: bool
    execution_status: str  # EXECUTED | NOT_EXECUTED | FAILED
    execution_time_ms: Optional[float] = None
    status: str  # DRIFT_DETECTED | STABLE | NOT_EXECUTED
    reason: Optional[str] = None
    significance_level: float = 0.05
    d_threshold: float = 0.10
    decision_rule: str = "p < 0.05 AND D >= 0.10"
    columns_tested: int = 0
    drift_detected_count: int = 0
    columns: list[dict[str, Any]] = []
    explanation: str = "The current distribution was compared with the historical baseline using the KS two-sample test."


class MLDetectionMethodsResponse(BaseModel):
    z_score: dict[str, Any]
    iqr: dict[str, Any]
    isolation_forest: dict[str, Any]
    ks_test: dict[str, Any]


class MLDetectionProofResponse(BaseModel):
    inspection_id: str
    dataset: str
    created_at: Optional[str] = None
    methods: MLDetectionMethodsResponse
