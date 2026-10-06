"""
Automated Test Suite for ML Detection Proofs & Individual Method Evidence
Compliant with DataGuard 2.0 Auditable Evidence Specification:
- Z-Score statistical proof
- IQR outlier proof
- Isolation Forest unsupervised ML decision score proof
- Kolmogorov-Smirnov Two-Sample Test proof (executed vs transparent NOT_EXECUTED)
- Finding ID linkage and API responses
"""

import math
import random
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.inspection_run import InspectionRun
from app.models.ml_detection_proof import MLDetectionProof
from app.ml.statistical_detector import StatisticalAnomalyDetector
from app.ml.isolation_forest import IsolationForestDetector
from app.agents.drift.drift_agent import DriftAgent
from app.services.ml_proof_service import MLProofService
from app.services.inspection_service import InspectionService


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def test_z_score_proof():
    """
    Test 1: Controlled dataset with known extreme value.
    Verifies mean, standard deviation, z-score calculation, and threshold |z| > 3.0.
    """
    random.seed(42)
    # 50 normal rows with values around 10.0 (std dev approx 0.5)
    data = [{"val": 10.0 + random.gauss(0, 0.5)} for _ in range(50)]
    # 1 extreme outlier at row index 50 with value 100.0
    data.append({"val": 100.0})

    detector = StatisticalAnomalyDetector()
    res = detector.detect_outliers(data, columns=["val"])
    proof = res.get("z_score_proof")

    assert proof is not None, "Z-Score proof must be returned"
    assert proof["executed"] is True
    assert proof["execution_status"] == "EXECUTED"
    assert proof["status"] == "ANOMALY_DETECTED"
    assert proof["formula"] == "z = (x - mean) / standard_deviation"
    assert proof["threshold"] == "|z| > 3.0"
    assert proof["columns_analyzed"] == 1
    assert proof["total_flagged_count"] >= 1

    col_proof = proof["columns"][0]
    assert col_proof["column"] == "val"
    assert col_proof["sample_size"] == 51
    assert col_proof["mean"] > 10.0
    assert col_proof["std_dev"] > 0.0
    assert col_proof["max_z_score"] > 3.0

    flagged_rows = [f["row_index"] for f in col_proof["flagged_values"]]
    assert 50 in flagged_rows, "Row 50 (value 100.0) must be flagged"

    # Verify formula math directly
    row_50_val = 100.0
    expected_z = (row_50_val - col_proof["mean"]) / col_proof["std_dev"]
    actual_z = next(f["z_score"] for f in col_proof["flagged_values"] if f["row_index"] == 50)
    assert math.isclose(expected_z, actual_z, rel_tol=1e-3)


def test_iqr_proof():
    """
    Test 2: Controlled dataset with known outlier outside 1.5 * IQR fences.
    Verifies Q1, Q3, IQR, lower_bound, upper_bound calculations.
    """
    # 40 rows between 10.0 and 20.0
    data = [{"amount": 10.0 + i * 0.25} for i in range(40)]
    # Injected outlier at index 40 with value 150.0
    data.append({"amount": 150.0})

    detector = StatisticalAnomalyDetector()
    res = detector.detect_outliers(data, columns=["amount"])
    iqr_proof = res.get("iqr_proof")

    assert iqr_proof is not None
    assert iqr_proof["executed"] is True
    assert iqr_proof["execution_status"] == "EXECUTED"
    assert iqr_proof["status"] == "OUTLIER_DETECTED"
    assert iqr_proof["multiplier"] == 1.5
    assert "IQR = Q3 - Q1" in iqr_proof["formulas"]

    col_proof = iqr_proof["columns"][0]
    assert col_proof["column"] == "amount"
    assert col_proof["sample_size"] == 41
    assert col_proof["q3"] > col_proof["q1"]
    assert col_proof["iqr"] == pytest.approx(col_proof["q3"] - col_proof["q1"], rel=1e-3)
    assert col_proof["upper_bound"] == pytest.approx(col_proof["q3"] + 1.5 * col_proof["iqr"], rel=1e-3)

    outlier_indices = [o["row_index"] for o in col_proof["outliers"]]
    assert 40 in outlier_indices, "Row index 40 must be identified as an IQR outlier"


def test_isolation_forest_proof():
    """
    Test 3: Multivariate Isolation Forest on controlled dataset.
    Verifies execution, model parameters, prediction definition, and separation threshold.
    Confirms NO fake accuracy metrics.
    """
    random.seed(42)
    data = []
    for _ in range(60):
        data.append({
            "feature_a": random.uniform(10.0, 20.0),
            "feature_b": random.uniform(50.0, 70.0),
        })
    # Injected multidimensional anomaly
    data.append({
        "feature_a": 999.0,
        "feature_b": -500.0,
    })

    detector = IsolationForestDetector(n_estimators=50, random_state=42)
    res = detector.detect(data, numeric_columns=["feature_a", "feature_b"])
    proof = res.get("isolation_forest_proof")

    assert proof is not None, "Isolation Forest proof must be returned"
    assert proof["executed"] is True
    assert proof["execution_status"] == "EXECUTED"
    assert proof["method"] == "Isolation Forest"
    assert proof["prediction_definition"] == "-1 = anomaly, 1 = normal"
    assert proof["model_parameters"]["n_estimators"] == 50
    assert proof["model_parameters"]["random_state"] == 42
    assert "separation_threshold" in proof
    assert proof["samples"] == 61
    assert proof["features_count"] == 2
    assert proof["anomalies_detected"] >= 1

    # Verify absence of fabricated accuracy / confidence metrics
    assert "accuracy" not in proof
    assert "precision" not in proof
    assert "f1_score" not in proof

    flagged_indices = [a["row_index"] for a in proof["flagged_anomalies"]]
    assert 60 in flagged_indices, "Injected multivariate anomaly at row 60 must be detected"


def test_ks_proof_with_baseline():
    """
    Test 4: Controlled baseline vs. shifted sample.
    Verifies scipy.stats.ks_2samp execution, D-statistic, p-value, and decision rule.
    """
    random.seed(42)
    # Baseline: Normal distribution centered at 10.0
    baseline = [{"metric": random.gauss(10.0, 1.0)} for _ in range(60)]
    # Current batch: Severely shifted distribution centered at 25.0
    current = [{"metric": random.gauss(25.0, 1.0)} for _ in range(60)]

    drift_agent = DriftAgent()
    result = drift_agent.analyze_drift(current, reference_rows=baseline)

    ks_proof = result.get("ks_proof")
    assert ks_proof is not None
    assert ks_proof["executed"] is True
    assert ks_proof["execution_status"] == "EXECUTED"
    assert ks_proof["status"] == "DRIFT_DETECTED"
    assert ks_proof["decision_rule"] == "p < 0.05 AND D >= 0.10"
    assert ks_proof["columns_tested"] == 1
    assert ks_proof["drift_detected_count"] == 1

    col_proof = ks_proof["columns"][0]
    assert col_proof["column"] == "metric"
    assert col_proof["ks_statistic"] > 0.5, "Severely shifted distributions must have large D"
    assert col_proof["p_value"] < 0.001
    assert col_proof["decision"] == "DRIFT DETECTED"
    assert col_proof["is_drift"] is True
    assert len(col_proof["cdf_curve"]) > 0


def test_ks_no_baseline_transparent_reporting():
    """
    Test 5: Transparent reporting when baseline is absent or insufficient.
    Verifies that DataGuard reports NOT_EXECUTED rather than fabricating a fake baseline.
    """
    current = [{"metric": 10.0 + i} for i in range(25)]

    drift_agent = DriftAgent()
    # Scenario A: Baseline is None
    result_none = drift_agent.analyze_drift(current, reference_rows=None)
    ks_proof_none = result_none.get("ks_proof")

    assert ks_proof_none["executed"] is False
    assert ks_proof_none["execution_status"] == "NOT_EXECUTED"
    assert ks_proof_none["status"] == "NOT_EXECUTED"
    assert ks_proof_none["reason"] == "historical baseline unavailable"

    # Scenario B: Baseline has fewer than 10 rows
    result_small = drift_agent.analyze_drift(current, reference_rows=[{"metric": 1.0}, {"metric": 2.0}])
    ks_proof_small = result_small.get("ks_proof")

    assert ks_proof_small["executed"] is False
    assert ks_proof_small["execution_status"] == "NOT_EXECUTED"
    assert "historical baseline unavailable" in ks_proof_small["reason"].lower()


def test_api_endpoints(client, db_session):
    """
    Test 6: Verify GET endpoints for ML Detection Proof.
    - GET /agents/audits/{id}/ml-proof
    - GET /agents/audits/latest/ml-proof
    - GET /audits/{inspection_id}/ml-proof
    """
    import os
    import json
    from app.models.user import User
    from app.core.security import create_access_token, hash_password

    # Ensure a valid user exists in DB for token authentication
    user = db_session.query(User).filter(User.is_active == True).first()
    if not user:
        user = User(
            id=uuid4(),
            email=f"ml_test_{uuid4().hex[:6]}@dataguard.ai",
            full_name="ML Test Engineer",
            hashed_password=hash_password("ValidPassword123!"),
            role="DATA_ENGINEER",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
        "email": user.email,
    })
    headers = {"Authorization": f"Bearer {token}"}

    demo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "demo", "guide_demo.csv"))
    if not os.path.exists(demo_path):
        demo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "olist", "olist_order_items_dataset.csv"))

    service = InspectionService()
    result = service.inspect_dataset_and_persist(
        db=db_session,
        dataset_path=os.path.abspath(demo_path),
    )
    assert result is not None
    inspection_id = result["inspection_id"]

    # 1. Test /agents/audits/{inspection_id}/ml-proof
    resp = client.get(f"/agents/audits/{inspection_id}/ml-proof", headers=headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert data["inspection_id"] == inspection_id
    assert "methods" in data
    assert "z_score" in data["methods"]
    assert "iqr" in data["methods"]
    assert "isolation_forest" in data["methods"]
    assert "ks_test" in data["methods"]

    # 2. Test /agents/audits/latest/ml-proof
    resp_latest = client.get("/agents/audits/latest/ml-proof", headers=headers)
    assert resp_latest.status_code == 200
    data_latest = resp_latest.json()
    assert "inspection_id" in data_latest
    assert "methods" in data_latest

    # 3. Test /audits/{inspection_id}/ml-proof
    resp_compat = client.get(f"/audits/{inspection_id}/ml-proof", headers=headers)
    assert resp_compat.status_code == 200
    assert resp_compat.json()["inspection_id"] == inspection_id


def test_proof_persistence_in_database(db_session):
    """
    Test 7: Verify MLDetectionProof records are persisted in PostgreSQL mldetectionproofs table.
    """
    import json

    latest_run = db_session.query(InspectionRun).order_by(InspectionRun.created_at.desc()).first()
    assert latest_run is not None, "An InspectionRun must exist"

    # Query mldetectionproofs table
    proofs = db_session.query(MLDetectionProof).filter(
        MLDetectionProof.inspection_id == latest_run.id
    ).all()

    assert len(proofs) >= 3, f"Expected at least 3 method proofs persisted, found {len(proofs)}"
    methods_found = {p.method for p in proofs}
    assert {"Z_SCORE", "IQR", "ISOLATION_FOREST"}.issubset(methods_found)
    for p in proofs:
        assert p.execution_status in ["EXECUTED", "NOT_EXECUTED", "NOT_APPLICABLE"]
        assert isinstance(p.evidence, str)
        ev = json.loads(p.evidence)
        assert isinstance(ev, dict)
