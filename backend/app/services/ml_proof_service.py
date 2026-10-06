import json
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.inspection_finding import InspectionFinding
from app.models.inspection_run import InspectionRun
from app.models.ml_detection_proof import MLDetectionProof


class MLProofService:
    """
    Service for constructing, persisting, and retrieving auditable,
    method-by-method mathematical and machine learning detection evidence.
    """

    @staticmethod
    def persist_ml_proofs(
        db: Session,
        inspection_run: InspectionRun,
        ml_proof_data: dict[str, Any],
        persisted_findings: list[InspectionFinding],
    ) -> list[MLDetectionProof]:
        """
        Persists separate individual proofs for Z-score, IQR, Isolation Forest, and KS test.
        Links each proof to the inspection run and to specific findings where applicable.
        """
        created_proofs: list[MLDetectionProof] = []

        # Map findings by (finding_type, column_name)
        finding_map: dict[tuple[str, Optional[str]], UUID] = {}
        for f in persisted_findings:
            key = (f.finding_type, f.column_name)
            finding_map[key] = f.id
            if f.finding_type == "ML_ISOLATION_FOREST_ANOMALY":
                finding_map[("ML_ISOLATION_FOREST_ANOMALY", None)] = f.id

        # -----------------------------------------------------------------
        # 1. Z-SCORE PROOFS
        # -----------------------------------------------------------------
        z_data = ml_proof_data.get("z_score", {})
        z_columns = z_data.get("columns", [])
        if z_columns:
            for col_info in z_columns:
                col_name = col_info.get("column")
                finding_id = finding_map.get(("NUMERICAL_OUTLIERS", col_name))
                if finding_id:
                    col_info["related_finding_id"] = str(finding_id)

                proof = MLDetectionProof(
                    inspection_id=inspection_run.id,
                    dataset_path=inspection_run.dataset_path,
                    method="Z_SCORE",
                    agent="Inspector Agent",
                    column_name=col_name,
                    execution_status=z_data.get("execution_status", "EXECUTED"),
                    status=col_info.get("status", "HEALTHY"),
                    sample_size=col_info.get("sample_size"),
                    mean=col_info.get("mean"),
                    std_dev=col_info.get("std_dev"),
                    threshold=col_info.get("threshold"),
                    flagged_count=col_info.get("flagged_count", 0),
                    execution_time_ms=z_data.get("execution_time_ms"),
                    evidence=json.dumps(col_info, default=str),
                    finding_id=finding_id,
                )
                db.add(proof)
                created_proofs.append(proof)
        elif z_data:
            proof = MLDetectionProof(
                inspection_id=inspection_run.id,
                dataset_path=inspection_run.dataset_path,
                method="Z_SCORE",
                agent="Inspector Agent",
                execution_status=z_data.get("execution_status", "NOT_APPLICABLE"),
                status=z_data.get("status", "NOT_APPLICABLE"),
                evidence=json.dumps(z_data, default=str),
            )
            db.add(proof)
            created_proofs.append(proof)

        # -----------------------------------------------------------------
        # 2. IQR PROOFS
        # -----------------------------------------------------------------
        iqr_data = ml_proof_data.get("iqr", {})
        iqr_columns = iqr_data.get("columns", [])
        if iqr_columns:
            for col_info in iqr_columns:
                col_name = col_info.get("column")
                finding_id = finding_map.get(("NUMERICAL_OUTLIERS", col_name))
                if finding_id:
                    col_info["related_finding_id"] = str(finding_id)

                proof = MLDetectionProof(
                    inspection_id=inspection_run.id,
                    dataset_path=inspection_run.dataset_path,
                    method="IQR",
                    agent="Inspector Agent",
                    column_name=col_name,
                    execution_status=iqr_data.get("execution_status", "EXECUTED"),
                    status=col_info.get("status", "HEALTHY"),
                    sample_size=col_info.get("sample_size"),
                    q1=col_info.get("q1"),
                    q3=col_info.get("q3"),
                    iqr=col_info.get("iqr"),
                    lower_bound=col_info.get("lower_bound"),
                    upper_bound=col_info.get("upper_bound"),
                    flagged_count=col_info.get("outlier_count", 0),
                    execution_time_ms=iqr_data.get("execution_time_ms"),
                    evidence=json.dumps(col_info, default=str),
                    finding_id=finding_id,
                )
                db.add(proof)
                created_proofs.append(proof)
        elif iqr_data:
            proof = MLDetectionProof(
                inspection_id=inspection_run.id,
                dataset_path=inspection_run.dataset_path,
                method="IQR",
                agent="Inspector Agent",
                execution_status=iqr_data.get("execution_status", "NOT_APPLICABLE"),
                status=iqr_data.get("status", "NOT_APPLICABLE"),
                evidence=json.dumps(iqr_data, default=str),
            )
            db.add(proof)
            created_proofs.append(proof)

        # -----------------------------------------------------------------
        # 3. ISOLATION FOREST PROOF
        # -----------------------------------------------------------------
        if_data = ml_proof_data.get("isolation_forest", {})
        if if_data:
            if_finding_id = finding_map.get(("ML_ISOLATION_FOREST_ANOMALY", None))
            if if_finding_id:
                if_data["related_finding_id"] = str(if_finding_id)

            proof = MLDetectionProof(
                inspection_id=inspection_run.id,
                dataset_path=inspection_run.dataset_path,
                method="ISOLATION_FOREST",
                agent="Inspector Agent",
                execution_status=if_data.get("execution_status", "EXECUTED"),
                status=if_data.get("status", "HEALTHY"),
                sample_size=if_data.get("samples"),
                anomaly_score=if_data.get("score_range", {}).get("min"),
                contamination=str(if_data.get("contamination", "auto")),
                flagged_count=if_data.get("anomalies_detected", 0),
                execution_time_ms=if_data.get("execution_time_ms"),
                evidence=json.dumps(if_data, default=str),
                finding_id=if_finding_id,
            )
            db.add(proof)
            created_proofs.append(proof)

        # -----------------------------------------------------------------
        # 4. KS TWO-SAMPLE TEST PROOFS
        # -----------------------------------------------------------------
        ks_data = ml_proof_data.get("ks_test", {})
        ks_columns = ks_data.get("columns", [])
        if ks_columns:
            for col_info in ks_columns:
                col_name = col_info.get("column")
                finding_id = finding_map.get(("DISTRIBUTION_DRIFT", col_name))
                if finding_id:
                    col_info["related_finding_id"] = str(finding_id)

                proof = MLDetectionProof(
                    inspection_id=inspection_run.id,
                    dataset_path=inspection_run.dataset_path,
                    method="KS_TEST",
                    agent="Drift Agent",
                    column_name=col_name,
                    execution_status=ks_data.get("execution_status", "EXECUTED"),
                    status="DRIFT_DETECTED" if col_info.get("is_drift") else "STABLE",
                    baseline_sample_size=col_info.get("baseline_sample_size"),
                    current_sample_size=col_info.get("current_sample_size"),
                    ks_statistic=col_info.get("ks_statistic"),
                    p_value=col_info.get("p_value"),
                    threshold=f"p<{col_info.get('significance_level', 0.05)} AND D>={col_info.get('d_threshold', 0.10)}",
                    flagged_count=1 if col_info.get("is_drift") else 0,
                    execution_time_ms=ks_data.get("execution_time_ms"),
                    evidence=json.dumps(col_info, default=str),
                    finding_id=finding_id,
                )
                db.add(proof)
                created_proofs.append(proof)
        elif ks_data:
            proof = MLDetectionProof(
                inspection_id=inspection_run.id,
                dataset_path=inspection_run.dataset_path,
                method="KS_TEST",
                agent="Drift Agent",
                execution_status=ks_data.get("execution_status", "NOT_EXECUTED"),
                status=ks_data.get("status", "NOT_EXECUTED"),
                threshold=ks_data.get("decision_rule", "p < 0.05 AND D >= 0.10"),
                execution_time_ms=ks_data.get("execution_time_ms"),
                evidence=json.dumps(ks_data, default=str),
            )
            db.add(proof)
            created_proofs.append(proof)

        db.commit()
        return created_proofs

    @staticmethod
    def get_ml_proof_response(
        db: Session,
        inspection_id: UUID,
    ) -> dict[str, Any]:
        """
        Retrieves persisted ML and statistical proofs for an inspection run.
        If proofs are not yet stored in mldetectionproofs, executes actual
        algorithms on dataset to generate and persist real mathematical proofs.
        """
        run = db.query(InspectionRun).filter(InspectionRun.id == inspection_id).first()
        if not run:
            raise ValueError(f"Inspection run '{inspection_id}' not found.")

        proof_records = (
            db.query(MLDetectionProof)
            .filter(MLDetectionProof.inspection_id == inspection_id)
            .order_by(MLDetectionProof.created_at.asc())
            .all()
        )

        if not proof_records:
            # Generate real proof from dataset
            return MLProofService._generate_and_persist_for_run(db, run)

        # Assemble methods dictionary from persisted records
        z_proof_records = [p for p in proof_records if p.method == "Z_SCORE"]
        iqr_proof_records = [p for p in proof_records if p.method == "IQR"]
        if_proof_records = [p for p in proof_records if p.method == "ISOLATION_FOREST"]
        ks_proof_records = [p for p in proof_records if p.method == "KS_TEST"]

        # Parse Z-Score
        z_columns = []
        for p in z_proof_records:
            if p.column_name:
                try:
                    ev = json.loads(p.evidence) if p.evidence else {}
                except Exception:
                    ev = {}
                ev["column"] = p.column_name
                ev["sample_size"] = p.sample_size or ev.get("sample_size")
                ev["mean"] = p.mean or ev.get("mean")
                ev["std_dev"] = p.std_dev or ev.get("std_dev")
                ev["threshold"] = p.threshold or ev.get("threshold", "|z| > 3.0")
                ev["status"] = p.status
                ev["flagged_count"] = p.flagged_count
                if p.finding_id:
                    ev["related_finding_id"] = str(p.finding_id)
                z_columns.append(ev)

        total_z_flagged = sum(c.get("flagged_count", 0) for c in z_columns)
        max_overall_z = max([c.get("max_z_score", 0.0) for c in z_columns], default=0.0)
        has_z = len(z_columns) > 0
        z_exec_time = z_proof_records[0].execution_time_ms if z_proof_records else 0.0

        z_method = {
            "method": "Z-Score",
            "agent": "Inspector Agent",
            "classification": "Statistical anomaly detection",
            "executed": has_z,
            "execution_status": "EXECUTED" if has_z else "NOT_APPLICABLE",
            "execution_time_ms": z_exec_time,
            "status": "ANOMALY_DETECTED" if total_z_flagged > 0 else "HEALTHY",
            "columns_analyzed": len(z_columns),
            "total_flagged_count": total_z_flagged,
            "max_z_score": max_overall_z,
            "threshold": "|z| > 3.0",
            "threshold_value": 3.0,
            "formula": "z = (x - mean) / standard_deviation",
            "explanation": "The value is more than 3 standard deviations from the calculated mean.",
            "columns": z_columns,
        }

        # Parse IQR
        iqr_columns = []
        for p in iqr_proof_records:
            if p.column_name:
                try:
                    ev = json.loads(p.evidence) if p.evidence else {}
                except Exception:
                    ev = {}
                ev["column"] = p.column_name
                ev["observations"] = p.sample_size or ev.get("observations")
                ev["sample_size"] = p.sample_size or ev.get("sample_size")
                ev["q1"] = p.q1 or ev.get("q1")
                ev["q3"] = p.q3 or ev.get("q3")
                ev["iqr"] = p.iqr or ev.get("iqr")
                ev["lower_bound"] = p.lower_bound or ev.get("lower_bound")
                ev["upper_bound"] = p.upper_bound or ev.get("upper_bound")
                ev["outlier_count"] = p.flagged_count
                ev["status"] = p.status
                if p.finding_id:
                    ev["related_finding_id"] = str(p.finding_id)
                iqr_columns.append(ev)

        total_iqr_outliers = sum(c.get("outlier_count", 0) for c in iqr_columns)
        has_iqr = len(iqr_columns) > 0
        iqr_exec_time = iqr_proof_records[0].execution_time_ms if iqr_proof_records else 0.0

        iqr_method = {
            "method": "IQR",
            "agent": "Inspector Agent",
            "classification": "Statistical outlier detection",
            "executed": has_iqr,
            "execution_status": "EXECUTED" if has_iqr else "NOT_APPLICABLE",
            "execution_time_ms": iqr_exec_time,
            "status": "OUTLIER_DETECTED" if total_iqr_outliers > 0 else "HEALTHY",
            "columns_analyzed": len(iqr_columns),
            "total_outliers_count": total_iqr_outliers,
            "method_rule": "1.5 × IQR",
            "formulas": [
                "IQR = Q3 - Q1",
                "Lower Bound = Q1 - 1.5 × IQR",
                "Upper Bound = Q3 + 1.5 × IQR",
            ],
            "explanation": "The observed value lies outside the IQR-based acceptable range.",
            "columns": iqr_columns,
        }

        # Parse Isolation Forest
        if if_proof_records:
            if_rec = if_proof_records[0]
            try:
                if_ev = json.loads(if_rec.evidence) if if_rec.evidence else {}
            except Exception:
                if_ev = {}
            if if_rec.finding_id:
                if_ev["related_finding_id"] = str(if_rec.finding_id)
            if_method = if_ev
        else:
            if_method = {
                "method": "Isolation Forest",
                "agent": "Inspector Agent",
                "classification": "Machine-learning-based unsupervised anomaly detection",
                "executed": False,
                "execution_status": "NOT_APPLICABLE",
                "status": "NOT_APPLICABLE",
                "reason": "Isolation Forest was not executed on this dataset.",
                "features": [],
                "features_count": 0,
                "samples": run.row_count,
                "anomalies_detected": 0,
                "contamination": "auto",
            }

        # Parse KS Test
        ks_columns = []
        ks_status = "NOT_EXECUTED"
        ks_execution_status = "NOT_EXECUTED"
        ks_reason = "historical baseline unavailable"
        ks_exec_time = 0.0

        for p in ks_proof_records:
            if p.column_name:
                try:
                    ev = json.loads(p.evidence) if p.evidence else {}
                except Exception:
                    ev = {}
                ev["column"] = p.column_name
                ev["baseline_sample_size"] = p.baseline_sample_size or ev.get("baseline_sample_size")
                ev["current_sample_size"] = p.current_sample_size or ev.get("current_sample_size")
                ev["ks_statistic"] = p.ks_statistic or ev.get("ks_statistic")
                ev["p_value"] = p.p_value or ev.get("p_value")
                ev["decision"] = p.status
                if p.finding_id:
                    ev["related_finding_id"] = str(p.finding_id)
                ks_columns.append(ev)
                ks_status = "DRIFT_DETECTED" if p.status == "DRIFT_DETECTED" else ks_status
                ks_execution_status = "EXECUTED"
                ks_exec_time = p.execution_time_ms or ks_exec_time
            else:
                try:
                    raw_ev = json.loads(p.evidence) if p.evidence else {}
                    ks_reason = raw_ev.get("reason", ks_reason)
                except Exception:
                    pass

        has_ks = len(ks_columns) > 0
        drift_detected_count = sum(1 for c in ks_columns if c.get("decision") == "DRIFT_DETECTED" or c.get("is_drift"))

        if has_ks:
            ks_method = {
                "method": "Kolmogorov-Smirnov Two-Sample Test",
                "agent": "Drift Agent",
                "classification": "Statistical distribution drift detection",
                "executed": True,
                "execution_status": "EXECUTED",
                "execution_time_ms": ks_exec_time,
                "status": "DRIFT_DETECTED" if drift_detected_count > 0 else "STABLE",
                "significance_level": 0.05,
                "d_threshold": 0.10,
                "decision_rule": "p < 0.05 AND D >= 0.10",
                "columns_tested": len(ks_columns),
                "drift_detected_count": drift_detected_count,
                "columns": ks_columns,
                "explanation": "The current distribution was compared with the historical baseline using the KS two-sample test.",
            }
        else:
            ks_method = {
                "method": "Kolmogorov-Smirnov Two-Sample Test",
                "agent": "Drift Agent",
                "classification": "Statistical distribution drift detection",
                "executed": False,
                "execution_status": "NOT_EXECUTED",
                "status": "NOT_EXECUTED",
                "reason": ks_reason,
                "significance_level": 0.05,
                "d_threshold": 0.10,
                "decision_rule": "p < 0.05 AND D >= 0.10",
                "columns_tested": 0,
                "drift_detected_count": 0,
                "columns": [],
                "explanation": "The Kolmogorov-Smirnov test requires a reference baseline distribution to evaluate drift. Baseline unavailable.",
            }

        return {
            "inspection_id": str(run.id),
            "dataset": run.dataset_path,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "methods": {
                "z_score": z_method,
                "iqr": iqr_method,
                "isolation_forest": if_method,
                "ks_test": ks_method,
            },
        }

    @staticmethod
    def _generate_and_persist_for_run(
        db: Session,
        run: InspectionRun,
    ) -> dict[str, Any]:
        """
        Executes actual algorithms on dataset for an existing run that didn't have proofs persisted yet,
        persisting proofs immediately.
        """
        from app.etl.extractor.dataset_loader import DatasetLoader
        from app.ml.ml_engine import MLEngine
        from app.agents.drift.drift_agent import DriftAgent
        from app.services.baseline_service import BaselineService

        try:
            rows = DatasetLoader.load_dataset(run.dataset_path, limit=2000)
        except Exception:
            rows = []

        baseline = BaselineService.get_baseline(db, run.dataset_path)
        ref_rows = baseline.reference_sample if baseline else None

        ml_engine = MLEngine()
        ml_res = ml_engine.analyze(rows=rows, reference_rows=ref_rows)

        drift_agent = DriftAgent()
        drift_res = drift_agent.execute(current_rows=rows, reference_rows=ref_rows)

        unified_proof = ml_res.get("ml_proof", {})
        unified_proof["ks_test"] = drift_res.get("ks_test_proof", {})

        findings_records = (
            db.query(InspectionFinding)
            .filter(InspectionFinding.inspection_id == run.id)
            .all()
        )

        MLProofService.persist_ml_proofs(
            db=db,
            inspection_run=run,
            ml_proof_data=unified_proof,
            persisted_findings=findings_records,
        )

        return MLProofService.get_ml_proof_response(db, run.id)
