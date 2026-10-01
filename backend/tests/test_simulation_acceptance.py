"""
DataGuard Phase 1 Acceptance Tests: Fault-Injection Simulation and Detector Correctness.
Verifies that:
1. CLEAN mode on olist_orders_dataset.csv returns audit_status HEALTHY with zero findings.
2. MISSING_VALUES returns 'MISSING_VALUES'.
3. DUPLICATES returns 'DUPLICATE_RECORDS'.
4. SCHEMA_DRIFT returns 'COLUMN_REMOVED'.
5. ML_OUTLIERS returns 'ML_ISOLATION_FOREST_ANOMALY'.
6. DISASTER returns all matching fault modes.
"""

import pytest
from app.etl.simulator import ETLSimulator


def test_simulation_clean_mode():
    res = ETLSimulator.run_simulation(
        dataset_path="olist/olist_orders_dataset.csv",
        mode="CLEAN",
        sample_size=500,
    )
    audit = res["audit"]
    assert audit.get("audit_status") == "HEALTHY"
    findings = audit.get("inspection", {}).get("findings", [])
    assert len(findings) == 0


def test_simulation_missing_values_mode():
    res = ETLSimulator.run_simulation(
        dataset_path="olist/olist_orders_dataset.csv",
        mode="MISSING_VALUES",
        sample_size=500,
    )
    audit = res["audit"]
    assert audit.get("audit_status") == "ANOMALY_DETECTED"
    finding_types = [f.get("type") for f in audit.get("inspection", {}).get("findings", [])]
    assert "MISSING_VALUES" in finding_types


def test_simulation_duplicates_mode():
    res = ETLSimulator.run_simulation(
        dataset_path="olist/olist_orders_dataset.csv",
        mode="DUPLICATES",
        sample_size=500,
    )
    audit = res["audit"]
    assert audit.get("audit_status") == "ANOMALY_DETECTED"
    finding_types = [f.get("type") for f in audit.get("inspection", {}).get("findings", [])]
    assert "DUPLICATE_RECORDS" in finding_types


def test_simulation_schema_drift_mode():
    res = ETLSimulator.run_simulation(
        dataset_path="olist/olist_orders_dataset.csv",
        mode="SCHEMA_DRIFT",
        sample_size=500,
    )
    audit = res["audit"]
    assert audit.get("audit_status") == "ANOMALY_DETECTED"
    finding_types = [f.get("type") for f in audit.get("inspection", {}).get("findings", [])]
    assert "COLUMN_REMOVED" in finding_types


def test_simulation_ml_outliers_mode():
    res = ETLSimulator.run_simulation(
        dataset_path="olist/olist_orders_dataset.csv",
        mode="ML_OUTLIERS",
        sample_size=500,
    )
    audit = res["audit"]
    assert audit.get("audit_status") == "ANOMALY_DETECTED"
    finding_types = [f.get("type") for f in audit.get("inspection", {}).get("findings", [])]
    assert "ML_ISOLATION_FOREST_ANOMALY" in finding_types or "NUMERICAL_OUTLIERS" in finding_types


def test_simulation_disaster_mode():
    res = ETLSimulator.run_simulation(
        dataset_path="olist/olist_orders_dataset.csv",
        mode="DISASTER",
        sample_size=500,
    )
    audit = res["audit"]
    assert audit.get("audit_status") == "ANOMALY_DETECTED"
    finding_types = [f.get("type") for f in audit.get("inspection", {}).get("findings", [])]
    assert "MISSING_VALUES" in finding_types
    assert "DUPLICATE_RECORDS" in finding_types
    assert "COLUMN_REMOVED" in finding_types
    assert "ML_ISOLATION_FOREST_ANOMALY" in finding_types
