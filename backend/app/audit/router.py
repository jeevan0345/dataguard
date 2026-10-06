from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.audit.anomaly import analyze_run
from app.audit.finding_service import ETLFindingService
from app.audit.root_cause import analyze_run_root_cause
from app.audit.schemas import (
    ETLRunCreate,
    ETLRunResponse,
    ETLRunUpdate,
)
from app.audit.service import ETLAuditService
from app.database.session import get_db
from app.schemas.inspection import (
    InspectionRequest,
    InspectionResponse,
)
from app.services.inspection_service import InspectionService


router = APIRouter(
    prefix="/audit",
    tags=["ETL Audit"],
)


# =========================================================
# CREATE ETL RUN
# =========================================================

@router.post(
    "/runs",
    response_model=ETLRunResponse,
    status_code=201,
)
def create_etl_run(
    payload: ETLRunCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new ETL pipeline execution record.
    """

    return ETLAuditService.create_run(
        db=db,
        pipeline_id=payload.pipeline_id,
        dataset_id=payload.dataset_id,
        started_at=payload.started_at,
        status=payload.status,
        rows_input=payload.rows_input,
        rows_output=payload.rows_output,
        duration_ms=payload.duration_ms,
        error_message=payload.error_message,
        checkpoint=payload.checkpoint,
    )


# =========================================================
# UPDATE ETL RUN
# =========================================================

@router.patch(
    "/runs/{run_id}",
    response_model=ETLRunResponse,
)
def update_etl_run(
    run_id: UUID,
    payload: ETLRunUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing ETL pipeline execution.
    """

    run = ETLAuditService.update_run(
        db=db,
        run_id=run_id,
        completed_at=payload.completed_at,
        status=payload.status,
        rows_input=payload.rows_input,
        rows_output=payload.rows_output,
        duration_ms=payload.duration_ms,
        error_message=payload.error_message,
        checkpoint=payload.checkpoint,
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="ETL run not found",
        )

    return run


# =========================================================
# GET SINGLE ETL RUN
# =========================================================

@router.get(
    "/runs/{run_id}",
    response_model=ETLRunResponse,
)
def get_etl_run(
    run_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieve one ETL pipeline execution.
    """

    run = ETLAuditService.get_run(
        db=db,
        run_id=run_id,
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="ETL run not found",
        )

    return run


# =========================================================
# LIST ETL RUNS
# =========================================================

@router.get(
    "/runs",
    response_model=list[ETLRunResponse],
)
def list_etl_runs(
    pipeline_id: Optional[str] = Query(
        default=None,
    ),
    dataset_id: Optional[str] = Query(
        default=None,
    ),
    status: Optional[str] = Query(
        default=None,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve historical ETL executions.
    """

    return ETLAuditService.get_runs(
        db=db,
        pipeline_id=pipeline_id,
        dataset_id=dataset_id,
        status=status,
        limit=limit,
    )


# =========================================================
# ANALYZE ETL RUN
# =========================================================

@router.get(
    "/runs/{run_id}/analyze",
)
def analyze_etl_run(
    run_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Analyze a completed ETL run against its historical baseline.
    """

    try:
        result = analyze_run(
            db=db,
            run_id=str(run_id),
        )

        return {
            "run_id": result.run_id,
            "pipeline_id": result.pipeline_id,
            "dataset_id": result.dataset_id,
            "is_anomaly": result.is_anomaly,
            "anomaly_score": result.anomaly_score,
            "summary": result.summary,
            "metrics": [
                {
                    "metric": metric.metric,
                    "actual": metric.actual,
                    "average": metric.average,
                    "lower_bound": metric.lower_bound,
                    "upper_bound": metric.upper_bound,
                    "deviation": metric.deviation,
                    "is_anomaly": metric.is_anomaly,
                    "explanation": metric.explanation,
                }
                for metric in result.metrics
            ],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# GENERATE AND SAVE ETL FINDINGS
# =========================================================

@router.get(
    "/runs/{run_id}/findings",
)
def get_etl_findings(
    run_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Analyze an ETL run, generate structured findings,
    persist them in PostgreSQL, and return them.
    """

    try:
        findings = ETLFindingService.generate_and_save_findings(
            db=db,
            run_id=run_id,
        )

        return {
            "run_id": str(run_id),
            "finding_count": len(findings),
            "findings": [
                {
                    "id": str(finding.id),
                    "run_id": str(finding.run_id),
                    "metric": finding.metric,
                    "finding_type": finding.finding_type,
                    "severity": finding.severity,
                    "actual_value": finding.actual_value,
                    "expected_average": finding.expected_average,
                    "lower_bound": finding.lower_bound,
                    "upper_bound": finding.upper_bound,
                    "deviation": finding.deviation,
                    "evidence": finding.evidence,
                    "likely_area": finding.likely_area,
                    "explanation": finding.explanation,
                    "created_at": finding.created_at,
                    "updated_at": finding.updated_at,
                    "is_active": finding.is_active,
                }
                for finding in findings
            ],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# ROOT CAUSE ANALYSIS
# =========================================================

@router.get(
    "/runs/{run_id}/root-cause",
)
def get_root_cause(
    run_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Analyze persisted findings and generate
    root-cause candidates.
    """

    try:
        result = analyze_run_root_cause(
            db=db,
            run_id=run_id,
        )

        return {
            "run_id": result.run_id,
            "finding_count": result.finding_count,
            "primary_cause": result.primary_cause,
            "overall_confidence": result.overall_confidence,
            "summary": result.summary,
            "candidates": [
                {
                    "cause": candidate.cause,
                    "confidence": candidate.confidence,
                    "evidence": candidate.evidence,
                    "affected_area": candidate.affected_area,
                    "explanation": candidate.explanation,
                }
                for candidate in result.candidates
            ],
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# DATASET INSPECTION
# =========================================================

@router.post(
    "/inspect",
    response_model=InspectionResponse,
)
def inspect_dataset(
    payload: InspectionRequest,
    db: Session = Depends(get_db),
):
    """
    Run the DataGuard Inspector Agent against a dataset
    and persist the inspection result into PostgreSQL.

    Workflow:

        Dataset
            ↓
        DatasetLoader
            ↓
        SchemaInference
            ↓
        InspectorAgent
            ↓
        Data Quality + Schema Drift
            ↓
        Unified Inspection Result
            ↓
        InspectionFindingService
            ↓
        PostgreSQL
            ↓
        API Response
    """

    try:
        service = InspectionService()

        result = service.inspect_dataset_and_persist(
            db=db,
            dataset_path=payload.dataset_path,
            expected_schema=payload.expected_schema,
        )

        return result

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =========================================================
# ML DETECTION PROOF
# =========================================================

@router.get(
    "/runs/{run_id}/ml-proof",
)
def get_ml_detection_proof(
    run_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieve auditable mathematical and ML detection proofs for an inspection run.
    """
    from app.services.ml_proof_service import MLProofService
    try:
        return MLProofService.get_ml_proof_response(db=db, inspection_id=run_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )