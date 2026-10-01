"""
DataGuard Multi-Agent & Product Routes
Provides API endpoints for agent orchestration, simulation, copilot chat, recovery, reports, and dashboard metrics.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from uuid import UUID
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user, require_role
from app.models.user import User
from app.etl.extractor.dataset_loader import DatasetLoader
from app.etl.extractor.schema_inference import SchemaInference
from app.agents.orchestrator import MultiAgentOrchestrator
from app.agents.copilot.copilot_agent import CopilotAgent
from app.agents.recovery.recovery_agent import RecoveryAgent
from app.audit.verification import VerificationEngine
from app.etl.simulator import ETLSimulator
from app.notifications.service import NotificationService
from app.models.inspection_run import InspectionRun
from app.models.inspection_finding import InspectionFinding
from app.services.inspection_finding_service import InspectionFindingService
from app.services.baseline_service import BaselineService
from app.evidence.evidence_builder import EvidenceBuilder
from app.agents.root_cause.root_cause_agent import RootCauseAgent
from app.agents.recommendation.recommendation_agent import RecommendationAgent
from app.audit.models import ETLRun, ETLFinding

router = APIRouter(
    prefix="/agents",
    tags=["Multi-Agent System & Product Operations"],
)


def _friendly_dataset_name(path: str) -> str:
    p = str(path).lower()
    if "order_item" in p:
        return "Order Items"
    elif "order_payment" in p:
        return "Order Payments"
    elif "order_review" in p:
        return "Order Reviews"
    elif "orders" in p:
        return "Orders Stream"
    elif "customer" in p:
        return "Customers"
    elif "product" in p:
        return "Products Catalog"
    elif "anomaly" in p or "test" in p:
        return "Synthetic Benchmark"
    elif "upload" in p:
        base = os.path.basename(path)
        return f"Upload: {base}"
    else:
        return os.path.basename(path) or path


def _build_dossier_from_run(db: Session, run: InspectionRun) -> dict[str, Any]:
    findings_records = (
        db.query(InspectionFinding)
        .filter(InspectionFinding.inspection_id == run.id)
        .order_by(InspectionFinding.created_at.asc())
        .all()
    )

    findings = []
    for f in findings_records:
        ev = {}
        if f.evidence:
            try:
                ev = json.loads(f.evidence) if isinstance(f.evidence, str) else f.evidence
            except Exception:
                ev = {"raw": f.evidence}
        findings.append({
            "type": f.finding_type,
            "severity": f.severity,
            "message": f.message,
            "column": f.column_name,
            "evidence": ev,
        })

    inspection_dict = {
        "agent": "Inspector Agent",
        "status": run.status,
        "highest_severity": run.highest_severity or "NONE",
        "finding_count": len(findings),
        "findings": findings,
    }

    evidence_res = EvidenceBuilder().build(inspection_dict)
    rca_res = RootCauseAgent().execute(evidence_data=evidence_res)
    rec_res = RecommendationAgent().execute(findings=findings, root_cause_summary=rca_res)
    recovery_res = RecoveryAgent().execute(findings=findings, rows=[])

    # Discover generated reports
    reports_info = None
    reports_dir = Path("reports")
    if reports_dir.exists():
        pdf_files = list(reports_dir.glob("*.pdf"))
        excel_files = list(reports_dir.glob("*.xlsx"))
        if pdf_files and excel_files:
            latest_pdf = max(pdf_files, key=os.path.getmtime)
            latest_excel = max(excel_files, key=os.path.getmtime)
            reports_info = {
                "pdf_report_path": str(latest_pdf),
                "pdf_filename": latest_pdf.name,
                "excel_report_path": str(latest_excel),
                "excel_filename": latest_excel.name,
                "generated_at": datetime.fromtimestamp(os.path.getmtime(latest_pdf)).isoformat(),
            }

    return {
        "id": str(run.id),
        "audit_status": run.status,
        "highest_severity": run.highest_severity or "NONE",
        "dataset_path": run.dataset_path,
        "friendly_name": _friendly_dataset_name(run.dataset_path),
        "row_count": run.row_count,
        "column_count": run.column_count,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "inspection": inspection_dict,
        "evidence": evidence_res,
        "root_cause": rca_res,
        "recommendations": rec_res,
        "recovery": recovery_res,
        "reports": reports_info,
    }


class OrchestrateRequest(BaseModel):
    dataset_path: str = Field(..., min_length=1, example="olist/olist_orders_dataset.csv")
    expected_schema: Optional[dict[str, str]] = None
    limit: Optional[int] = Field(default=1000, ge=10, le=100000)


class SimulationRequest(BaseModel):
    dataset_path: str = Field(default="olist/olist_orders_dataset.csv")
    mode: str = Field(default="MISSING_VALUES", pattern="^(CLEAN|MISSING_VALUES|DUPLICATES|SCHEMA_DRIFT|ML_OUTLIERS|DISASTER)$")
    sample_size: int = Field(default=500, ge=50, le=5000)


class CopilotChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    context: Optional[dict[str, Any]] = None


class RecoveryExecuteRequest(BaseModel):
    dataset_path: str
    actions: list[dict[str, Any]]
    expected_schema: Optional[dict[str, str]] = None


# Cache last active audit result for copilot contextual fallback
_active_audit_context: dict[str, Any] = {}


@router.post("/orchestrate")
def orchestrate_audit(
    payload: OrchestrateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "DATA_ENGINEER")),
):
    """
    Triggers the complete DataGuard 7-agent swarm:
    Inspector -> Drift -> Evidence -> Root Cause -> Recommendation -> Recovery -> Reporter.
    Persists findings to PostgreSQL.
    """
    global _active_audit_context
    try:
        rows = DatasetLoader.load_dataset(payload.dataset_path)
        if not rows:
            raise HTTPException(status_code=404, detail=f"Dataset '{payload.dataset_path}' is empty or not found.")

        rows_subset = rows[:payload.limit] if payload.limit else rows
        actual_schema = SchemaInference.infer_schema(rows_subset)

        # Baseline lifecycle: Check existing baseline for dataset; if first audit, create baseline
        baseline = BaselineService.get_baseline(db, payload.dataset_path)
        reference_rows = None
        if baseline:
            expected_schema = payload.expected_schema or baseline.expected_schema
            reference_rows = baseline.reference_sample
        else:
            expected_schema = payload.expected_schema or actual_schema
            BaselineService.set_baseline(
                db=db,
                dataset_path=payload.dataset_path,
                rows=rows_subset,
                schema=actual_schema,
            )

        orchestrator = MultiAgentOrchestrator()
        result = orchestrator.audit_dataset(
            rows=rows_subset,
            expected_schema=expected_schema,
            actual_schema=actual_schema,
            reference_rows=reference_rows,
            dataset_path=payload.dataset_path,
            generate_reports=True,
        )

        # Persist inspection into PostgreSQL
        inspection_run = InspectionFindingService.save_inspection(
            db=db,
            dataset_path=payload.dataset_path,
            inspection_result=result["inspection"],
            row_count=len(rows_subset),
            column_count=len(actual_schema),
        )

        result["id"] = str(inspection_run.id)
        result["inspection_id"] = str(inspection_run.id)
        result["created_at"] = inspection_run.created_at.isoformat() if inspection_run.created_at else None
        result["friendly_name"] = _friendly_dataset_name(payload.dataset_path)

        _active_audit_context = result
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/audits/{inspection_id}/set-baseline")
def set_audit_as_baseline(
    inspection_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "DATA_ENGINEER")),
):
    """
    Sets the specified inspection run as the active historical baseline for its dataset path.
    Updates expected schema and reference sample in PostgreSQL.
    """
    run = db.query(InspectionRun).filter(InspectionRun.id == inspection_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Inspection run not found.")

    try:
        rows = DatasetLoader.load_dataset(run.dataset_path)
    except Exception:
        rows = []

    actual_schema = SchemaInference.infer_schema(rows[:500]) if rows else {}
    baseline = BaselineService.set_baseline(
        db=db,
        dataset_path=run.dataset_path,
        rows=rows[:500],
        schema=actual_schema,
    )

    return {
        "status": "SUCCESS",
        "message": f"Successfully set inspection {inspection_id} as baseline for '{run.dataset_path}'.",
        "baseline": {
            "id": str(baseline.id),
            "dataset_path": baseline.dataset_path,
            "expected_schema": baseline.expected_schema,
            "sample_row_count": baseline.sample_row_count,
            "updated_at": baseline.updated_at.isoformat() if baseline.updated_at else None,
        },
    }


@router.post("/simulate")
def run_simulation(
    payload: SimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "DATA_ENGINEER")),
):
    """
    Executes a simulated ETL pipeline run with selectable fault injection.
    Persists generated inspection run into PostgreSQL.
    """
    global _active_audit_context
    try:
        sim_result = ETLSimulator.run_simulation(
            dataset_path=payload.dataset_path,
            mode=payload.mode,
            sample_size=payload.sample_size,
        )

        audit_res = sim_result.get("audit", {})
        if audit_res and "inspection" in audit_res:
            col_count = audit_res.get("column_count", 0)
            inspection_run = InspectionFindingService.save_inspection(
                db=db,
                dataset_path=payload.dataset_path,
                inspection_result=audit_res["inspection"],
                row_count=sim_result.get("final_row_count", payload.sample_size),
                column_count=col_count,
            )
            audit_res["id"] = str(inspection_run.id)
            audit_res["inspection_id"] = str(inspection_run.id)
            audit_res["created_at"] = inspection_run.created_at.isoformat() if inspection_run.created_at else None
            audit_res["friendly_name"] = _friendly_dataset_name(payload.dataset_path)
            sim_result["audit"] = audit_res

        _active_audit_context = sim_result.get("audit", {})
        return sim_result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/copilot/chat")
def copilot_chat(
    payload: CopilotChatRequest,
    db: Session = Depends(get_db),
):
    """
    Interactive AI assistant for Data Engineers.
    Answers natural language queries strictly grounded in stored audit evidence.
    Loads latest persisted audit from PostgreSQL if context is not supplied.
    """
    agent = CopilotAgent()
    context = payload.context or _active_audit_context

    # Fallback to latest persisted audit in database if active context is empty
    if not context or not context.get("inspection"):
        latest_run = (
            db.query(InspectionRun)
            .order_by(InspectionRun.created_at.desc())
            .first()
        )
        if latest_run:
            context = _build_dossier_from_run(db, latest_run)

    return agent.chat(
        query=payload.query,
        audit_context=context,
    )


@router.post("/recovery/execute")
def execute_and_verify_recovery(
    payload: RecoveryExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "DATA_ENGINEER")),
):
    """
    Applies proposed recovery actions and runs the Verification Engine
    to issue a certified PASS/FAIL audit sign-off.
    Enforces policy checks and primary key protection.
    Persists the post-remediation audit to PostgreSQL.
    """
    try:
        # Policy Check: Protect Primary Keys & ID columns from arbitrary removal
        for act in payload.actions:
            target = str(act.get("target", "")).lower()
            atype = act.get("action_type")
            if atype in ["QUARANTINE_NULL_RECORDS", "DEDUPLICATE_ROWS"] and (target.endswith("_id") or target == "id" or target.endswith("_key")):
                # High severity policy check
                if act.get("risk_level") == "HIGH" and current_user.role != "ADMIN":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"High-risk remediation action on primary key column '{act.get('target')}' requires ADMIN approval.",
                    )

        rows = DatasetLoader.load_dataset(payload.dataset_path)
        sample = rows[:500]
        actual_schema = SchemaInference.infer_schema(sample)
        expected_schema = payload.expected_schema or actual_schema

        # Pre-recovery inspection
        orchestrator = MultiAgentOrchestrator()
        pre_audit = orchestrator.inspector_agent.execute(
            rows=sample,
            expected_schema=expected_schema,
            actual_schema=actual_schema,
        )

        # Apply recovery actions
        recovery_agent = RecoveryAgent()
        remediated_rows = recovery_agent.execute_recovery(sample, payload.actions)

        # Post-recovery inspection
        post_schema = SchemaInference.infer_schema(remediated_rows)
        post_audit = orchestrator.inspector_agent.execute(
            rows=remediated_rows,
            expected_schema=expected_schema,
            actual_schema=post_schema,
        )

        # Verification Engine Verdict
        verdict_res = VerificationEngine.verify(
            before_inspection=pre_audit,
            after_inspection=post_audit,
            original_row_count=len(sample),
            remediated_row_count=len(remediated_rows),
        )

        # Persist post-recovery inspection record into PostgreSQL
        post_run = InspectionFindingService.save_inspection(
            db=db,
            dataset_path=payload.dataset_path + " (Remediated)",
            inspection_result=post_audit,
            row_count=len(remediated_rows),
            column_count=len(post_schema),
        )

        return {
            "status": "RECOVERY_APPLIED",
            "verdict": verdict_res["verdict"],
            "verification": verdict_res,
            "remediated_sample_count": len(remediated_rows),
            "remediated_inspection_id": str(post_run.id),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status")
def get_agents_status():
    """
    Returns dynamic live operational status of all seven agents from orchestrator.
    """
    orchestrator = MultiAgentOrchestrator()
    agents = orchestrator.get_swarm_status()
    return {
        "active_agents": len(agents),
        "total_agents": len(agents),
        "status": "OPERATIONAL",
        "agents": agents,
    }


@router.get("/health")
def get_system_health(db: Session = Depends(get_db)):
    """
    Pings PostgreSQL and inspects runtime architecture truth.
    """
    pg_status = "DISCONNECTED"
    try:
        db.execute(text("SELECT 1"))
        pg_status = "CONNECTED"
    except Exception:
        pg_status = "ERROR"

    return {
        "status": "HEALTHY" if pg_status == "CONNECTED" else "UNHEALTHY",
        "postgres": pg_status,
        "profiling_runtime": "Automated On-Demand Profiling (Standalone Synchronous Runtime)",
        "redis_celery": "STANDALONE / IDLE",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/audits/latest")
def get_latest_audit(db: Session = Depends(get_db)):
    """
    Retrieves the most recent persisted audit dossier from PostgreSQL.
    """
    latest_run = (
        db.query(InspectionRun)
        .order_by(InspectionRun.created_at.desc())
        .first()
    )
    if not latest_run:
        raise HTTPException(status_code=404, detail="No persisted audit records found.")

    return _build_dossier_from_run(db, latest_run)


@router.get("/audits/{inspection_id}")
def get_audit_by_id(inspection_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieves a specific persisted audit dossier by its UUID from PostgreSQL.
    """
    run = (
        db.query(InspectionRun)
        .filter(InspectionRun.id == inspection_id)
        .first()
    )
    if not run:
        raise HTTPException(status_code=404, detail="Audit dossier not found.")

    return _build_dossier_from_run(db, run)


@router.get("/audits")
def list_audits(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Lists recent historical audits for UI selection dropdowns.
    """
    runs = (
        db.query(InspectionRun)
        .order_by(InspectionRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "dataset_path": r.dataset_path,
            "friendly_name": _friendly_dataset_name(r.dataset_path),
            "status": r.status,
            "highest_severity": r.highest_severity or "NONE",
            "finding_count": r.finding_count,
            "row_count": r.row_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]


@router.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    """
    Lists real generated PDF and Excel audit report files from storage.
    """
    reports_dir = Path("reports")
    if not reports_dir.exists():
        return []

    report_files = []
    for file in sorted(reports_dir.iterdir(), key=os.path.getmtime, reverse=True):
        if file.suffix.lower() in [".pdf", ".xlsx"]:
            report_type = "PDF" if file.suffix.lower() == ".pdf" else "EXCEL"
            report_files.append({
                "filename": file.name,
                "report_type": report_type,
                "size_bytes": file.stat().st_size,
                "generated_at": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                "download_url": f"/agents/reports/download/{file.name}",
            })

    return report_files


@router.get("/reports/download/{filename}")
def download_report(filename: str):
    """
    Downloads an executive PDF or Excel audit report.
    """
    # Prevent path traversal
    safe_name = Path(filename).name
    filepath = os.path.join("reports", safe_name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Requested report file does not exist.")

    media_type = "application/pdf" if filename.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return FileResponse(
        path=filepath,
        filename=safe_name,
        media_type=media_type,
    )


@router.get("/alerts")
def get_operational_alerts(unread_only: bool = False):
    """
    Fetches operational notification alerts for the frontend dashboard.
    """
    return {
        "count": len(NotificationService.get_alerts(unread_only)),
        "alerts": NotificationService.get_alerts(unread_only),
    }


@router.post("/alerts/mark-read")
def mark_alerts_read():
    """
    Marks all notifications as read.
    """
    NotificationService.mark_all_read()
    return {"status": "SUCCESS", "message": "All alerts marked as read."}


@router.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Aggregates overall health KPIs, severity distributions, and recent runs for dashboard graphs.
    Health Index uses a deterministic documented formula based on real findings.
    """
    total_inspections = db.query(InspectionRun).count()
    total_findings = db.query(InspectionFinding).count()
    total_etl_runs = db.query(ETLRun).count()

    critical_count = db.query(InspectionFinding).filter(InspectionFinding.severity == "CRITICAL").count()
    high_count = db.query(InspectionFinding).filter(InspectionFinding.severity == "HIGH").count()
    medium_count = db.query(InspectionFinding).filter(InspectionFinding.severity == "MEDIUM").count()
    low_count = db.query(InspectionFinding).filter(InspectionFinding.severity == "LOW").count()

    recent_inspections = (
        db.query(InspectionRun)
        .order_by(InspectionRun.created_at.desc())
        .limit(10)
        .all()
    )

    # Calculate deterministic documented System Health Index (0 - 100)
    # Formula: Based on latest inspection run; if none, default 100%
    latest_run = recent_inspections[0] if recent_inspections else None
    if not latest_run:
        health_index = 100
        health_status = "OPTIMAL"
    else:
        latest_crit = db.query(InspectionFinding).filter(InspectionFinding.inspection_id == latest_run.id, InspectionFinding.severity == "CRITICAL").count()
        latest_high = db.query(InspectionFinding).filter(InspectionFinding.inspection_id == latest_run.id, InspectionFinding.severity == "HIGH").count()
        latest_med = db.query(InspectionFinding).filter(InspectionFinding.inspection_id == latest_run.id, InspectionFinding.severity == "MEDIUM").count()
        latest_low = db.query(InspectionFinding).filter(InspectionFinding.inspection_id == latest_run.id, InspectionFinding.severity == "LOW").count()

        penalty = (latest_crit * 20) + (latest_high * 10) + (latest_med * 3) + (latest_low * 1)
        health_index = max(0, min(100, 100 - penalty))
        health_status = "OPTIMAL" if health_index >= 85 else ("DEGRADED" if health_index >= 60 else "CRITICAL_ATTENTION")

    return {
        "health_index": health_index,
        "health_status": health_status,
        "health_formula": "100 - (CRITICAL*20 + HIGH*10 + MEDIUM*3 + LOW*1) on latest audit",
        "active_agents": 7,
        "total_agents": 7,
        "kpis": {
            "total_inspections": total_inspections,
            "total_findings": total_findings,
            "total_etl_runs": total_etl_runs,
            "critical_findings": critical_count,
            "high_findings": high_count,
            "medium_findings": medium_count,
            "low_findings": low_count,
        },
        "severity_distribution": [
            {"severity": "CRITICAL", "count": critical_count, "color": "#EF4444"},
            {"severity": "HIGH", "count": high_count, "color": "#F97316"},
            {"severity": "MEDIUM", "count": medium_count, "color": "#FBBF24"},
            {"severity": "LOW", "count": low_count, "color": "#3B82F6"},
        ],
        "recent_runs": [
            {
                "id": str(r.id),
                "dataset_path": r.dataset_path,
                "friendly_name": _friendly_dataset_name(r.dataset_path),
                "status": r.status,
                "highest_severity": r.highest_severity or "NONE",
                "row_count": r.row_count,
                "finding_count": r.finding_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent_inspections
        ],
    }
