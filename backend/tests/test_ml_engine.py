"""
Test suite for DataGuard ML Engine
"""

from app.etl.extractor.dataset_loader import DatasetLoader
from app.ml.ml_engine import MLEngine


def test_ml_engine_execution():
    rows = DatasetLoader.load_dataset("olist/olist_order_items_dataset.csv")
    assert len(rows) > 0, "Dataset should have rows"

    engine = MLEngine()
    sample = rows[:500]
    result = engine.analyze(sample)

    assert "status" in result
    assert "findings" in result
    assert "profile" in result
    assert "isolation_forest" in result
    print(f"Test passed! Status: {result['status']}, Findings: {result['finding_count']}")


if __name__ == "__main__":
    test_ml_engine_execution()
