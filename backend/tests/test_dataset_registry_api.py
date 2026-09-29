"""
Test Suite: DataGuard Dataset Registry, CORS Configuration, and Serialization
"""

import unittest
from uuid import uuid4, UUID
from datetime import datetime

from app.main import app
from app.api.dataset_registry_routes import (
    get_benchmarks,
    get_synthetic_scenarios,
    OLIST_BENCHMARKS,
    SYNTHETIC_SCENARIOS,
)
from app.schemas.dataset_registry import (
    DatasetRegistryResponse,
    DatasetRegistryBase,
)
from app.database.session import SessionLocal
from app.models.dataset_registry import DatasetRegistry
from app.services.dataset_registry_service import DatasetRegistryService


class TestDatasetRegistryAndCORS(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_cors_middleware_configuration(self):
        """
        Verify that CORSMiddleware is registered in app.user_middleware and explicitly
        authorizes http://localhost:3000 with credentials enabled without wildcard *.
        """
        from fastapi.middleware.cors import CORSMiddleware
        cors_middlewares = [m for m in app.user_middleware if m.cls == CORSMiddleware]
        self.assertGreater(len(cors_middlewares), 0, "CORSMiddleware must be registered in app")

        cors_mw = cors_middlewares[0]
        allow_origins = cors_mw.kwargs.get("allow_origins", [])
        allow_credentials = cors_mw.kwargs.get("allow_credentials", False)

        self.assertIn("http://localhost:3000", allow_origins, "Origin http://localhost:3000 must be allowed")
        self.assertTrue(allow_credentials, "allow_credentials must be True")
        self.assertNotIn("*", allow_origins, "Wildcard '*' must NOT be used with allow_credentials=True")

    def test_dataset_response_uuid_serialization(self):
        """
        Verify that DatasetRegistryResponse validates UUID instances without throwing ValidationError.
        """
        test_uuid = uuid4()
        now = datetime.utcnow()
        mock_record = {
            "id": test_uuid,
            "dataset_name": f"test_ds_{test_uuid.hex[:6]}",
            "dataset_type": "BENCHMARK",
            "source": "Olist Stream",
            "file_path": "olist/olist_orders_dataset.csv",
            "file_format": "csv",
            "row_count": 5000,
            "column_count": 8,
            "quality_score": 98.5,
            "status": "Registered",
            "uploaded_at": now,
            "last_profiled_at": now,
            "created_at": now,
            "is_active": True,
        }

        # Validates dictionary
        model = DatasetRegistryResponse.model_validate(mock_record)
        self.assertEqual(str(model.id), str(test_uuid))
        self.assertEqual(model.row_count, 5000)

        # Serializes cleanly to JSON dictionary
        dumped = model.model_dump(mode="json")
        self.assertIsInstance(dumped["id"], str)
        self.assertEqual(dumped["id"], str(test_uuid))

    def test_database_registry_rows_validation(self):
        """
        Verify that all persisted DatasetRegistry rows in PostgreSQL validate against DatasetRegistryResponse.
        """
        datasets = DatasetRegistryService.get_all_datasets(self.db)
        self.assertIsInstance(datasets, list)

        for ds in datasets:
            # model_validate directly from SQLAlchemy ORM instance
            validated = DatasetRegistryResponse.model_validate(ds)
            self.assertIsNotNone(validated.id)
            self.assertIsInstance(validated.dataset_name, str)
            self.assertIsInstance(validated.row_count, int)

    def test_olist_benchmarks_schema_alignment(self):
        """
        Verify get_benchmarks provides category, records, and tags expected by frontend DatasetsView.
        """
        benchmarks = get_benchmarks()
        self.assertGreaterEqual(len(benchmarks), 4)

        for b in benchmarks:
            self.assertIn("id", b)
            self.assertIn("name", b)
            self.assertIn("category", b)
            self.assertIn("records", b)
            self.assertIn("tags", b)
            self.assertIn("file_path", b)
            self.assertIsInstance(b["records"], int)
            self.assertGreater(b["records"], 0)
            self.assertIsInstance(b["tags"], list)
            self.assertGreater(len(b["tags"]), 0)

    def test_synthetic_scenarios_schema_alignment(self):
        """
        Verify get_synthetic_scenarios provides mode, name, category, and anomalies array.
        """
        scenarios = get_synthetic_scenarios()
        self.assertEqual(len(scenarios), 6)

        expected_modes = {"CLEAN", "MISSING_VALUES", "DUPLICATES", "SCHEMA_DRIFT", "ML_OUTLIERS", "DISASTER"}
        found_modes = set()

        for s in scenarios:
            self.assertIn("mode", s)
            self.assertIn("name", s)
            self.assertIn("category", s)
            self.assertIn("anomalies", s)
            self.assertIsInstance(s["anomalies"], list)
            self.assertGreater(len(s["anomalies"]), 0)
            found_modes.add(s["mode"])

        self.assertEqual(found_modes, expected_modes)


if __name__ == "__main__":
    unittest.main()
