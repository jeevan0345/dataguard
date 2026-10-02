from typing import Any


class DataQualityAgent:
    """
    Detects common dataset-level data-quality problems.

    Current checks:
    - Empty dataset
    - Missing values
    - Duplicate records

    Missing values include:
    - None
    - Empty strings
    - Whitespace-only strings
    """

    def __init__(self) -> None:
        self.agent_name = "Data Quality Agent"

    def inspect(
        self,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        findings = []

        # =====================================================
        # 1. EMPTY DATASET
        # =====================================================

        if not rows:
            findings.append(
                {
                    "type": "EMPTY_DATASET",
                    "severity": "CRITICAL",
                    "message": "The dataset contains no records.",
                    "evidence": {
                        "row_count": 0,
                    },
                }
            )

            return {
                "agent": self.agent_name,
                "status": "ANOMALY",
                "row_count": 0,
                "finding_count": len(findings),
                "findings": findings,
            }

        # =====================================================
        # 2. MISSING VALUES
        # =====================================================

        column_missing_counts: dict[str, int] = {}

        for row in rows:
            for column, value in row.items():

                if self._is_missing(value):
                    column_missing_counts[column] = (
                        column_missing_counts.get(column, 0) + 1
                    )

        for column, missing_count in column_missing_counts.items():

            missing_percentage = (
                missing_count / len(rows)
            ) * 100

            # ---------------------------------------------
            # Severity classification
            # ---------------------------------------------

            if missing_percentage >= 50:
                severity = "CRITICAL"

            elif missing_percentage >= 10:
                severity = "HIGH"

            elif missing_percentage >= 5:
                severity = "MEDIUM"

            else:
                severity = "LOW"

            findings.append(
                {
                    "type": "MISSING_VALUES",
                    "column": column,
                    "severity": severity,
                    "message": (
                        f"Column '{column}' contains "
                        f"{missing_count} missing value(s)."
                    ),
                    "evidence": {
                        "column": column,
                        "missing_count": missing_count,
                        "missing_percentage": round(
                            missing_percentage,
                            2,
                        ),
                        "total_rows": len(rows),
                    },
                }
            )

        # =====================================================
        # 3. DUPLICATE RECORDS
        # =====================================================

        seen_records = set()
        duplicate_count = 0

        for row in rows:

            record_key = tuple(
                sorted(
                    (
                        str(key),
                        str(value),
                    )
                    for key, value in row.items()
                )
            )

            if record_key in seen_records:
                duplicate_count += 1

            else:
                seen_records.add(record_key)

        if duplicate_count > 0:

            duplicate_percentage = (
                duplicate_count / len(rows)
            ) * 100

            # ---------------------------------------------
            # Severity classification
            # ---------------------------------------------

            if duplicate_percentage >= 20:
                severity = "CRITICAL"

            elif duplicate_percentage >= 10:
                severity = "HIGH"

            elif duplicate_percentage >= 5:
                severity = "MEDIUM"

            else:
                severity = "LOW"

            findings.append(
                {
                    "type": "DUPLICATE_RECORDS",
                    "severity": severity,
                    "message": (
                        f"Detected {duplicate_count} "
                        f"duplicate record(s)."
                    ),
                    "evidence": {
                        "duplicate_count": duplicate_count,
                        "duplicate_percentage": round(
                            duplicate_percentage,
                            2,
                        ),
                        "total_rows": len(rows),
                    },
                }
            )

        # =====================================================
        # 4. FINAL STATUS
        # =====================================================

        status = (
            "ANOMALY"
            if findings
            else "HEALTHY"
        )

        return {
            "agent": self.agent_name,
            "status": status,
            "row_count": len(rows),
            "finding_count": len(findings),
            "findings": findings,
        }

    # =========================================================
    # HELPER: MISSING VALUE DETECTION
    # =========================================================

    @staticmethod
    def _is_missing(
        value: Any,
    ) -> bool:
        """
        Determine whether a value should be treated
        as missing.

        Missing values:
        - None
        - ""
        - "   "
        """

        if value is None:
            return True

        if isinstance(value, str):
            return not value.strip()

        return False