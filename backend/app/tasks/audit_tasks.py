"""
DataGuard Asynchronous Celery Tasks
Executes background audits, periodic health monitoring, and report pre-generation.
"""

from app.core.celery_app import celery_app
from app.etl.extractor.dataset_loader import DatasetLoader
from app.etl.extractor.schema_inference import SchemaInference
from app.agents.orchestrator import MultiAgentOrchestrator
from app.database.session import SessionLocal
from app.services.baseline_service import BaselineService


@celery_app.task(name="tasks.run_background_inspection")
def run_background_inspection(dataset_path: str, limit: int = 2000):
    """
    Background worker task to audit a dataset asynchronously.
    Retrieves historical baseline schema and reference rows from PostgreSQL.
    """
    rows = DatasetLoader.load_dataset(dataset_path)
    sample = rows[:limit] if limit else rows
    schema = SchemaInference.infer_schema(sample)

    db = SessionLocal()
    reference_rows = None
    expected_schema = schema
    try:
        baseline = BaselineService.get_baseline(db, dataset_path)
        if baseline:
            expected_schema = baseline.expected_schema
            reference_rows = baseline.reference_sample
        else:
            BaselineService.set_baseline(
                db=db,
                dataset_path=dataset_path,
                rows=sample,
                schema=schema,
            )
    finally:
        db.close()

    orchestrator = MultiAgentOrchestrator()
    result = orchestrator.audit_dataset(
        rows=sample,
        expected_schema=expected_schema,
        actual_schema=schema,
        reference_rows=reference_rows,
        dataset_path=dataset_path,
        generate_reports=True,
    )
    return {
        "status": result["audit_status"],
        "dataset_path": dataset_path,
        "finding_count": len(result.get("inspection", {}).get("findings", [])),
    }


@celery_app.task(name="tasks.scheduled_health_check")
def scheduled_health_check():
    """
    Periodic job to ensure Olist pipeline datasets remain healthy.
    """
    return run_background_inspection("olist/olist_orders_dataset.csv", limit=500)
