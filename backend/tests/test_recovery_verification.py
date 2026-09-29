"""
Test Suite: DataGuard Controlled Recovery & Verification Engine
"""

import unittest
from app.agents.recovery.recovery_agent import RecoveryAgent
from app.audit.verification import VerificationEngine
from app.agents.orchestrator import MultiAgentOrchestrator
from app.agents.copilot.copilot_agent import CopilotAgent
from app.etl.extractor.dataset_loader import DatasetLoader


class TestRecoveryVerification(unittest.TestCase):

    def test_controlled_recovery_and_verification(self):
        # 1. Simulate corrupted dataset (with duplicates and missing values)
        sample_rows = [
            {"order_id": "ORD-001", "customer_id": "CUST-A", "amount": 100.0},
            {"order_id": "ORD-001", "customer_id": "CUST-A", "amount": 100.0},  # Duplicate
            {"order_id": "ORD-002", "customer_id": None, "amount": 250.0},       # Missing
            {"order_id": "ORD-003", "customer_id": "CUST-C", "amount": 300.0},
        ]

        findings = [
            {
                "type": "DUPLICATE_RECORDS",
                "severity": "CRITICAL",
                "evidence": {"duplicate_count": 1, "duplicate_percentage": 25.0},
            },
            {
                "type": "MISSING_VALUES",
                "severity": "HIGH",
                "evidence": {"column": "customer_id", "missing_count": 1, "missing_percentage": 25.0},
            },
        ]

        # 2. Recovery Agent proposes plan
        recovery_agent = RecoveryAgent(max_auto_quarantine_pct=15.0)
        plan = recovery_agent.propose_recovery(findings=findings, rows=sample_rows)

        self.assertEqual(plan["status"], "RECOVERY_PLAN_PROPOSED")
        self.assertEqual(len(plan["candidates"]), 2)

        # 3. Execute recovery
        remediated = recovery_agent.execute_recovery(sample_rows, plan["candidates"])

        # Check deduplication occurred
        self.assertEqual(len(remediated), 2)  # 1 duplicate removed, 1 null quarantined
        self.assertEqual(remediated[0]["order_id"], "ORD-001")
        self.assertEqual(remediated[1]["order_id"], "ORD-003")

        # 4. Verify post-remediation
        before_inspection = {"status": "ANOMALY_DETECTED", "findings": findings}
        after_inspection = {"status": "HEALTHY", "findings": []}

        verdict_res = VerificationEngine.verify(
            before_inspection=before_inspection,
            after_inspection=after_inspection,
            original_row_count=len(sample_rows),
            remediated_row_count=len(remediated),
        )

        self.assertEqual(verdict_res["verdict"], "PASS")
        self.assertEqual(verdict_res["metrics"]["resolved_finding_count"], 2)
        self.assertEqual(verdict_res["metrics"]["anomaly_reduction_rate_pct"], 100.0)
        self.assertTrue(verdict_res["audit_trail"]["signed_off"])


class TestMultiAgentSwarmAndSecurity(unittest.TestCase):

    def test_7_agent_swarm_status(self):
        orchestrator = MultiAgentOrchestrator()
        swarm = orchestrator.get_swarm_status()
        self.assertEqual(len(swarm), 7)
        agent_names = [a["name"] for a in swarm]
        expected_agents = [
            "Inspector Agent",
            "Drift Agent",
            "Root Cause Agent",
            "Recommendation Agent",
            "Recovery Agent",
            "Reporter Agent",
            "AI Copilot Agent",
        ]
        for name in expected_agents:
            self.assertIn(name, agent_names)

    def test_copilot_evidence_grounded_tiers(self):
        copilot = CopilotAgent()
        context = {
            "dataset_name": "Test Ingestion Stream",
            "audit_status": "ANOMALY_DETECTED",
            "inspection": {
                "highest_severity": "CRITICAL",
                "finding_count": 2,
                "findings": [
                    {"type": "MISSING_VALUES", "severity": "HIGH", "message": "Column order_id has 12 nulls", "column": "order_id"},
                    {"type": "DUPLICATE_RECORDS", "severity": "CRITICAL", "message": "5 duplicates detected"}
                ]
            },
            "evidence": {
                "evidence": [
                    {"evidence_id": "EV-001", "finding_type": "MISSING_VALUES", "message": "Missing order_id"},
                    {"evidence_id": "EV-002", "finding_type": "DUPLICATE_RECORDS", "message": "5 duplicates detected"}
                ]
            },
            "root_cause": {
                "primary_cause": "UPSTREAM_EXTRACTION_CORRUPTION",
                "overall_confidence": 0.92,
                "candidates": [{"cause": "UPSTREAM_EXTRACTION_CORRUPTION", "confidence": 0.92}]
            }
        }

        response = copilot.chat("What are the active findings and root cause?", context)
        self.assertIn("reply", response)
        self.assertIn("FACT", response["reply"])
        self.assertIn("CANDIDATE", response["reply"])
        self.assertIn("RECOMMENDATION", response["reply"])
        self.assertIn("UNKNOWN", response["reply"])
        self.assertIn("citations", response)
        self.assertTrue(len(response["citations"]) > 0)

    def test_path_traversal_rejection(self):
        with self.assertRaises(PermissionError):
            DatasetLoader.load_dataset("../../windows/system32/cmd.exe")


if __name__ == "__main__":
    unittest.main()
