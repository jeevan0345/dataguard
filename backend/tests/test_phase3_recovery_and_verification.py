"""
Test Suite: Phase 3 Recovery Safety, Remediated CSV Generation, and Cryptographic Hash Verification
"""

import os
import unittest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.user import User
from app.models.inspection_run import InspectionRun
from app.models.inspection_finding import InspectionFinding
from app.core.security import create_access_token, hash_password
from app.services.inspection_finding_service import InspectionFindingService
from app.evidence.evidence_builder import EvidenceBuilder


class TestPhase3RecoveryAndVerification(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Create test users: Admin and Data Engineer
        cls.admin_user = User(
            id=uuid4(),
            email=f"admin_{uuid4().hex[:6]}@dataguard.ai",
            full_name="Admin Tester",
            hashed_password=hash_password("AdminPass123!"),
            role="ADMIN",
            is_superuser=True,
            is_active=True,
        )
        cls.engineer_user = User(
            id=uuid4(),
            email=f"engineer_{uuid4().hex[:6]}@dataguard.ai",
            full_name="Engineer Tester",
            hashed_password=hash_password("EngPass123!"),
            role="DATA_ENGINEER",
            is_superuser=False,
            is_active=True,
        )
        cls.db.add(cls.admin_user)
        cls.db.add(cls.engineer_user)
        cls.db.commit()

        cls.admin_token = create_access_token({"sub": str(cls.admin_user.id), "role": "ADMIN", "email": cls.admin_user.email})
        cls.engineer_token = create_access_token({"sub": str(cls.engineer_user.id), "role": "DATA_ENGINEER", "email": cls.engineer_user.email})

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_cryptographic_hash_generation_and_tamper_verification(self):
        # 1. Create an inspection with findings
        inspection_result = {
            "status": "ANOMALY_DETECTED",
            "highest_severity": "CRITICAL",
            "findings": [
                {
                    "type": "MISSING_VALUES",
                    "severity": "CRITICAL",
                    "column": "order_id",
                    "message": "Column 'order_id' contains 10 nulls.",
                    "evidence": {"column": "order_id", "missing_count": 10},
                }
            ],
        }

        run = InspectionFindingService.save_inspection(
            db=self.db,
            dataset_path="olist/olist_orders_dataset.csv",
            inspection_result=inspection_result,
            row_count=100,
            column_count=5,
        )

        self.assertIsNotNone(run.audit_hash)
        self.assertIsNotNone(run.audit_hmac)
        self.assertEqual(len(run.audit_hash), 64)
        self.assertEqual(len(run.audit_hmac), 64)

        # 2. Verify audit via API -> Should be valid
        resp = self.client.get(
            f"/agents/audits/{run.id}/verify",
            headers={"Authorization": f"Bearer {self.engineer_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["stored_hash"], run.audit_hash)
        self.assertEqual(data["computed_hash"], run.audit_hash)

        # 3. Simulate database tampering: alter the finding message
        finding = self.db.query(InspectionFinding).filter(InspectionFinding.inspection_id == run.id).first()
        finding.message = "TAMPERED MESSAGE BY MALICIOUS ACTOR"
        self.db.commit()

        # 4. Verify again -> Must detect integrity violation!
        resp_tampered = self.client.get(
            f"/agents/audits/{run.id}/verify",
            headers={"Authorization": f"Bearer {self.engineer_token}"},
        )
        self.assertEqual(resp_tampered.status_code, 200)
        data_tampered = resp_tampered.json()
        self.assertFalse(data_tampered["valid"])
        self.assertNotEqual(data_tampered["stored_hash"], data_tampered["computed_hash"])
        self.assertIn("INTEGRITY VIOLATION", data_tampered["message"])

    def test_forged_recovery_actions_rejected(self):
        # Client attempts to send a forged/unauthorized action not proposed by RecoveryAgent
        payload = {
            "dataset_path": "olist/olist_orders_dataset.csv",
            "actions": [
                {
                    "action_id": "ACT-FORGED-999",
                    "action_type": "DROP_ENTIRE_DATABASE",
                    "target": "ALL_TABLES",
                    "action_parameters": {},
                }
            ],
        }

        resp = self.client.post(
            "/agents/recovery/execute",
            json=payload,
            headers={"Authorization": f"Bearer {self.engineer_token}"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not an authorized remediation candidate", resp.json()["detail"])

    def test_recovery_execution_generates_real_csv_and_allows_download(self):
        # Create an audit run with clean proposals
        inspection_result = {
            "status": "ANOMALY_DETECTED",
            "highest_severity": "MEDIUM",
            "findings": [
                {
                    "type": "DUPLICATE_RECORDS",
                    "severity": "MEDIUM",
                    "column": "order_id",
                    "message": "Duplicate rows detected.",
                    "evidence": {"duplicate_count": 2, "duplicate_percentage": 5.0},
                }
            ],
        }

        run = InspectionFindingService.save_inspection(
            db=self.db,
            dataset_path="olist/olist_orders_dataset.csv",
            inspection_result=inspection_result,
            row_count=500,
            column_count=8,
        )

        # Authorized candidate matching the proposal
        payload = {
            "dataset_path": "olist/olist_orders_dataset.csv",
            "audit_id": str(run.id),
            "actions": [
                {
                    "action_id": "ACT-001",
                    "action_type": "DEDUPLICATE_ROWS",
                    "target": "ALL_ROWS",
                }
            ],
        }

        resp = self.client.post(
            "/agents/recovery/execute",
            json=payload,
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["status"], "RECOVERY_APPLIED")
        self.assertIn("recovery_run_id", data)
        self.assertIn("download_url", data)
        self.assertIsNotNone(data["remediated_file_hash"])
        self.assertTrue(os.path.exists(data["remediated_file_path"]))

        # Download the remediated CSV file
        download_resp = self.client.get(
            data["download_url"],
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(download_resp.status_code, 200)
        self.assertIn("text/csv", download_resp.headers["content-type"])
        self.assertEqual(download_resp.headers.get("x-file-sha256"), data["remediated_file_hash"])
        self.assertTrue(len(download_resp.content) > 0)


if __name__ == "__main__":
    unittest.main()
