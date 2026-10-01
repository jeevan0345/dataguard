"""
DataGuard Baseline Service
Manages persistence, retrieval, and updating of per-dataset baselines in PostgreSQL.
Enables schema drift and KS distribution drift detection across successive uploads.
"""

import copy
from typing import Any, Optional
import numpy as np
from sqlalchemy.orm import Session
from app.models.dataset_baseline import DatasetBaseline
from app.etl.extractor.schema_inference import SchemaInference


class BaselineService:
    """
    CRUD and comparison logic for dataset baselines.
    """

    @staticmethod
    def get_baseline(db: Session, dataset_path: str) -> Optional[DatasetBaseline]:
        return (
            db.query(DatasetBaseline)
            .filter(DatasetBaseline.dataset_path == dataset_path)
            .first()
        )

    @classmethod
    def set_baseline(
        cls,
        db: Session,
        dataset_path: str,
        rows: list[dict[str, Any]],
        schema: Optional[dict[str, str]] = None,
        quality_score: float = 100.0,
    ) -> DatasetBaseline:
        """
        Stores or overwrites the baseline for a dataset path with the given rows & schema.
        Bounded to first 500 rows for memory and storage efficiency.
        """
        inferred_schema = schema or SchemaInference.infer_schema(rows)
        sample_rows = [copy.deepcopy(r) for r in rows[:500]] if rows else []

        # Build numeric summary for KS drift reference
        numeric_summary = {}
        if sample_rows:
            for col, dtype in inferred_schema.items():
                if dtype in ["integer", "float"]:
                    vals = []
                    for r in sample_rows:
                        try:
                            v = float(r.get(col))
                            if not (np.isnan(v) or np.isinf(v)):
                                vals.append(v)
                        except (ValueError, TypeError):
                            pass
                    if vals:
                        arr = np.array(vals)
                        numeric_summary[col] = {
                            "count": len(vals),
                            "mean": round(float(np.mean(arr)), 4),
                            "std": round(float(np.std(arr)), 4),
                            "min": round(float(np.min(arr)), 4),
                            "max": round(float(np.max(arr)), 4),
                        }

        existing = cls.get_baseline(db, dataset_path)
        if existing:
            existing.expected_schema = inferred_schema
            existing.reference_sample = sample_rows
            existing.numeric_summary = numeric_summary
            existing.quality_score = quality_score
            existing.sample_row_count = len(sample_rows)
            db.commit()
            db.refresh(existing)
            return existing

        baseline = DatasetBaseline(
            dataset_path=dataset_path,
            expected_schema=inferred_schema,
            reference_sample=sample_rows,
            numeric_summary=numeric_summary,
            quality_score=quality_score,
            sample_row_count=len(sample_rows),
        )
        db.add(baseline)
        db.commit()
        db.refresh(baseline)
        return baseline

    @classmethod
    def ensure_baseline(
        cls,
        db: Session,
        dataset_path: str,
        rows: list[dict[str, Any]],
        schema: Optional[dict[str, str]] = None,
        quality_score: float = 100.0,
    ) -> tuple[DatasetBaseline, bool]:
        """
        Returns (baseline, created). If baseline does not exist, creates it.
        """
        existing = cls.get_baseline(db, dataset_path)
        if existing:
            return existing, False

        new_baseline = cls.set_baseline(
            db=db,
            dataset_path=dataset_path,
            rows=rows,
            schema=schema,
            quality_score=quality_score,
        )
        return new_baseline, True
