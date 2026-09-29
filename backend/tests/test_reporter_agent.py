"""
Test Suite: DataGuard Reporter Agent PDF & Excel Generation
"""

import os
import unittest
from app.agents.reporter.reporter_agent import ReporterAgent


class TestReporterAgent(unittest.TestCase):

    def test_pdf_and_excel_generation(self):
        reporter = ReporterAgent(output_dir="reports")
        dummy_data = {
            "dataset_path": "test/sample_dataset.csv",
            "row_count": 1000,
            "column_count": 6,
            "inspection": {
                "status": "ANOMALY_DETECTED",
                "highest_severity": "CRITICAL",
                "findings": [
                    {
                        "type": "MISSING_VALUES",
                        "severity": "HIGH",
                        "message": "Column 'customer_id' contains missing values.",
                    },
                    {
                        "type": "DUPLICATE_RECORDS",
                        "severity": "CRITICAL",
                        "message": "Duplicate rows detected.",
                    },
                ],
            },
            "root_cause": {
                "primary_cause": "Upstream Extraction Contract Change",
                "overall_confidence": 0.92,
                "candidates": [
                    {
                        "cause": "Upstream Extraction Contract Change",
                        "confidence": 0.92,
                        "affected_area": "Extraction",
                    }
                ],
            },
        }

        res = reporter.generate_all_reports(dummy_data)
        self.assertEqual(res["status"], "REPORTS_GENERATED")
        self.assertTrue(os.path.exists(res["pdf_report_path"]))
        self.assertTrue(os.path.exists(res["excel_report_path"]))
        self.assertTrue(os.path.getsize(res["pdf_report_path"]) > 500)
        self.assertTrue(os.path.getsize(res["excel_report_path"]) > 500)


if __name__ == "__main__":
    unittest.main()
