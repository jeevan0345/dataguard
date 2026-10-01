import os
import re
from pathlib import Path
from uuid import UUID, uuid4
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.auth.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.dataset_registry import DatasetRegistry
from app.schemas.dataset_registry import (
    DatasetRegistryCreate,
    DatasetRegistryResponse,
    DatasetRegistryUpdate,
)
from app.services.dataset_registry_service import DatasetRegistryService
from app.etl.extractor.dataset_loader import DatasetLoader
from app.etl.extractor.schema_inference import SchemaInference
from app.ml.profiler import DatasetProfiler

router = APIRouter(
    prefix="/datasets",
    tags=["Dataset Registry"]
)

OLIST_BENCHMARKS = [
    {
        "id": "olist_orders",
        "name": "Olist Orders Stream",
        "category": "Orders",
        "records": 99441,
        "description": "E-commerce order lifecycle, states, purchase and delivery timestamps.",
        "file_path": "olist/olist_orders_dataset.csv",
        "format": "csv",
        "source_type": "BENCHMARK",
        "row_count": 99441,
        "column_count": 8,
        "is_benchmark": True,
        "tags": ["Transactions", "Lifecycle", "Timestamps"],
    },
    {
        "id": "olist_order_items",
        "name": "Olist Order Items",
        "category": "Items & Pricing",
        "records": 112650,
        "description": "Individual items, pricing, freight charges, and seller linkages.",
        "file_path": "olist/olist_order_items_dataset.csv",
        "format": "csv",
        "source_type": "BENCHMARK",
        "row_count": 112650,
        "column_count": 7,
        "is_benchmark": True,
        "tags": ["Pricing", "Freight", "Sellers"],
    },
    {
        "id": "olist_customers",
        "name": "Olist Customers",
        "category": "Customers",
        "records": 99441,
        "description": "Customer identification keys, zip code prefixes, state regions.",
        "file_path": "olist/olist_customers_dataset.csv",
        "format": "csv",
        "source_type": "BENCHMARK",
        "row_count": 99441,
        "column_count": 5,
        "is_benchmark": True,
        "tags": ["Geolocation", "Demographics", "States"],
    },
    {
        "id": "olist_products",
        "name": "Olist Products Catalog",
        "category": "Catalog",
        "records": 32951,
        "description": "Product categories, dimensions, weights, and photo counts.",
        "file_path": "olist/olist_products_dataset.csv",
        "format": "csv",
        "source_type": "BENCHMARK",
        "row_count": 32951,
        "column_count": 9,
        "is_benchmark": True,
        "tags": ["Catalog", "Weights", "Dimensions"],
    },
    {
        "id": "olist_payments",
        "name": "Olist Order Payments",
        "category": "Payments",
        "records": 103886,
        "description": "Payment types (credit card, voucher, boleto), installments, amounts.",
        "file_path": "olist/olist_order_payments_dataset.csv",
        "format": "csv",
        "source_type": "BENCHMARK",
        "row_count": 103886,
        "column_count": 5,
        "is_benchmark": True,
        "tags": ["Payment Types", "Installments", "Amounts"],
    },
    {
        "id": "olist_reviews",
        "name": "Olist Order Reviews",
        "category": "Customer Reviews",
        "records": 99224,
        "description": "Review ratings (1-5), customer comments, response timestamps.",
        "file_path": "olist/olist_order_reviews_dataset.csv",
        "format": "csv",
        "source_type": "BENCHMARK",
        "row_count": 99224,
        "column_count": 7,
        "is_benchmark": True,
        "tags": ["Sentiment", "Ratings", "Feedback"],
    },
]

SYNTHETIC_SCENARIOS = [
    {
        "id": "CLEAN",
        "mode": "CLEAN",
        "name": "Clean Baseline",
        "title": "Clean Baseline",
        "category": "Baseline",
        "description": "Simulates normal healthy ETL pipeline with zero injected anomalies.",
        "badge": "Normal",
        "severity": "NONE",
        "color": "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
        "anomalies": ["Zero anomalies injected", "Normal distributions preserved"],
    },
    {
        "id": "MISSING_VALUES",
        "mode": "MISSING_VALUES",
        "name": "Missing Values Injection",
        "title": "Missing Values Injection",
        "category": "Data Quality",
        "description": "Injects 20% null / empty strings into critical key columns.",
        "badge": "Quality Anomaly",
        "severity": "HIGH",
        "color": "border-amber-500/40 bg-amber-500/10 text-amber-300",
        "anomalies": ["20% null injection in key columns", "Empty string substitutions"],
    },
    {
        "id": "DUPLICATES",
        "mode": "DUPLICATES",
        "name": "Duplicate Records Surge",
        "title": "Duplicate Records Surge",
        "category": "Data Integrity",
        "description": "Injects duplicate transaction records simulating replay failure.",
        "badge": "Integrity Anomaly",
        "severity": "CRITICAL",
        "color": "border-red-500/40 bg-red-500/10 text-red-300",
        "anomalies": ["High-volume duplicate transactions", "Replay simulation"],
    },
    {
        "id": "SCHEMA_DRIFT",
        "mode": "SCHEMA_DRIFT",
        "name": "Breaking Schema Drift",
        "title": "Breaking Schema Drift",
        "category": "Schema Evolution",
        "description": "Removes an expected column from the extraction stream.",
        "badge": "Schema Drift",
        "severity": "CRITICAL",
        "color": "border-purple-500/40 bg-purple-500/10 text-purple-300",
        "anomalies": ["Column dropped without migration", "Schema contract failure"],
    },
    {
        "id": "ML_OUTLIERS",
        "mode": "ML_OUTLIERS",
        "name": "ML Numerical Outliers",
        "title": "ML Numerical Outliers",
        "category": "Machine Learning",
        "description": "Injects multivariate outliers detected by Isolation Forest.",
        "badge": "ML Anomaly",
        "severity": "HIGH",
        "color": "border-blue-500/40 bg-blue-500/10 text-blue-300",
        "anomalies": ["Multivariate statistical outliers", "Isolation Forest score spike"],
    },
    {
        "id": "DISASTER",
        "mode": "DISASTER",
        "name": "Composite Disaster Scenario",
        "title": "Composite Disaster Scenario",
        "category": "System Stress",
        "description": "Simultaneous multi-fault corruption: nulls + dups + schema break + outliers.",
        "badge": "Critical Multi-Fault",
        "severity": "CRITICAL",
        "color": "border-red-600/50 bg-red-900/20 text-red-400",
        "anomalies": ["Nulls + Duplicates + Schema Drift + Outliers", "Multi-fault pipeline stress"],
    },
]


@router.get("/benchmarks")
def get_benchmarks():
    """
    Returns included Olist benchmark datasets.
    Internal paths are abstracted so ordinary users interact with friendly identifiers.
    """
    return OLIST_BENCHMARKS


@router.get("/synthetic-scenarios")
def get_synthetic_scenarios():
    """
    Returns available synthetic anomaly scenarios for the Pipeline Simulator.
    """
    return SYNTHETIC_SCENARIOS


@router.post("/upload")
def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "DATA_ENGINEER")),
):
    """
    Upload a user dataset (CSV, JSON, XLSX).
    Validates extension and size, prevents path traversal, saves safely to server storage,
    infers metadata, and registers the dataset in PostgreSQL.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    ext = Path(file.filename).suffix.lower()
    allowed_extensions = [".csv", ".json", ".xlsx"]
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: CSV, JSON, XLSX.",
        )

    safe_base = re.sub(r"[^a-zA-Z0-9_\.-]", "_", Path(file.filename).stem)[:40]
    unique_name = f"{uuid4().hex[:8]}_{safe_base}{ext}"

    uploads_dir = DatasetLoader.DATASET_ROOT / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    destination_path = (uploads_dir / unique_name).resolve()

    try:
        destination_path.relative_to(DatasetLoader.DATASET_ROOT.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid destination path detected.")

    max_size = 50 * 1024 * 1024  # 50 MB limit
    total_size = 0

    with open(destination_path, "wb") as f_out:
        while chunk := file.file.read(1024 * 1024):
            total_size += len(chunk)
            if total_size > max_size:
                f_out.close()
                destination_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File size exceeds the 50MB limit.",
                )
            f_out.write(chunk)

    rel_path = f"uploads/{unique_name}"
    try:
        rows = DatasetLoader.load_dataset(rel_path)
        row_count = len(rows)
        col_count = len(rows[0].keys()) if rows else 0
    except Exception as exc:
        destination_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse uploaded {ext} file: {str(exc)}",
        )

    # Compute quality score based on profiler completeness and uniqueness
    profiler = DatasetProfiler()
    profile_res = profiler.profile(rows)
    total_cells = row_count * col_count if row_count and col_count else 1
    missing_cells = sum(
        c.get("missing_count", 0)
        for c in profile_res.get("columns", {}).values()
        if isinstance(c, dict)
    )

    seen_rows = set()
    dup_rows = 0
    for r in rows:
        t = tuple(sorted((k, str(v)) for k, v in r.items()))
        if t in seen_rows:
            dup_rows += 1
        else:
            seen_rows.add(t)

    completeness = max(0.0, 1.0 - (missing_cells / total_cells))
    uniqueness = max(0.0, 1.0 - (dup_rows / row_count)) if row_count > 0 else 1.0
    computed_quality_score = round(((completeness * 0.6) + (uniqueness * 0.4)) * 100, 2)

    dataset_entry = DatasetRegistry(
        dataset_name=f"{safe_base}_{uuid4().hex[:4]}",
        dataset_type="USER_UPLOAD",
        source="Browser File Upload",
        file_path=rel_path,
        file_format=ext.replace(".", ""),
        row_count=row_count,
        column_count=col_count,
        quality_score=computed_quality_score,
        status="Registered",
    )
    db.add(dataset_entry)
    db.commit()
    db.refresh(dataset_entry)

    return {
        "id": str(dataset_entry.id),
        "dataset_name": dataset_entry.dataset_name,
        "original_filename": file.filename,
        "file_path": rel_path,
        "file_format": dataset_entry.file_format,
        "file_size": total_size,
        "row_count": row_count,
        "column_count": col_count,
        "uploaded_at": dataset_entry.uploaded_at.isoformat(),
        "status": dataset_entry.status,
        "message": f"Successfully uploaded and registered {file.filename} ({row_count} rows, {col_count} cols).",
    }


@router.post(
    "/",
    response_model=DatasetRegistryResponse
)
def create_dataset(
    dataset: DatasetRegistryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "DATA_ENGINEER")),
):

    return DatasetRegistryService.create_dataset(db, dataset)


@router.get(
    "/",
    response_model=list[DatasetRegistryResponse]
)
def get_all_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return DatasetRegistryService.get_all_datasets(db)


@router.get(
    "/{dataset_id}",
    response_model=DatasetRegistryResponse
)
def get_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    dataset = DatasetRegistryService.get_dataset(
        db,
        str(dataset_id)
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    return dataset


@router.put(
    "/{dataset_id}",
    response_model=DatasetRegistryResponse
)
def update_dataset(
    dataset_id: UUID,
    dataset: DatasetRegistryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "DATA_ENGINEER")),
):

    updated = DatasetRegistryService.update_dataset(
        db,
        str(dataset_id),
        dataset
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    return updated


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ADMIN", "DATA_ENGINEER")),
):

    deleted = DatasetRegistryService.delete_dataset(
        db,
        str(dataset_id)
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    return {
        "message": "Dataset deleted successfully"
    }