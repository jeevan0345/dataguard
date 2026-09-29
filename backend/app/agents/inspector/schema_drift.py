from typing import Any


class SchemaDriftAgent:
    """
    Detects changes between an expected dataset schema
    and the schema observed in a new ETL run.

    This is a deterministic Inspector-side component.
    It does not use an LLM or Pandas.
    """

    def __init__(self) -> None:
        self.agent_name = "Schema Drift Agent"

    def inspect(
        self,
        expected_schema: dict[str, str],
        actual_schema: dict[str, str],
    ) -> dict[str, Any]:
        """
        Compare expected and actual schemas.

        Schema format:

        {
            "customer_id": "integer",
            "customer_name": "string",
            "amount": "float"
        }

        Returns structured findings for:
        - Removed columns
        - Added columns
        - Changed data types
        """

        findings: list[dict[str, Any]] = []

        expected_columns = set(expected_schema.keys())
        actual_columns = set(actual_schema.keys())

        # ---------------------------------------------------------
        # 1. Detect removed columns
        # ---------------------------------------------------------
        removed_columns = sorted(
            expected_columns - actual_columns
        )

        for column in removed_columns:
            findings.append(
                {
                    "type": "COLUMN_REMOVED",
                    "severity": "CRITICAL",
                    "message": (
                        f"Expected column '{column}' "
                        f"is missing from the actual schema."
                    ),
                    "evidence": {
                        "column": column,
                        "expected_type": expected_schema[column],
                        "actual_type": None,
                    },
                }
            )

        # ---------------------------------------------------------
        # 2. Detect added columns
        # ---------------------------------------------------------
        added_columns = sorted(
            actual_columns - expected_columns
        )

        for column in added_columns:
            findings.append(
                {
                    "type": "COLUMN_ADDED",
                    "severity": "MEDIUM",
                    "message": (
                        f"New column '{column}' was detected "
                        f"in the actual schema."
                    ),
                    "evidence": {
                        "column": column,
                        "expected_type": None,
                        "actual_type": actual_schema[column],
                    },
                }
            )

        # ---------------------------------------------------------
        # 3. Detect changed data types
        # ---------------------------------------------------------
        common_columns = sorted(
            expected_columns & actual_columns
        )

        for column in common_columns:

            expected_type = self._normalize_type(
                expected_schema[column]
            )

            actual_type = self._normalize_type(
                actual_schema[column]
            )

            if expected_type != actual_type:
                findings.append(
                    {
                        "type": "COLUMN_TYPE_CHANGED",
                        "severity": "HIGH",
                        "message": (
                            f"Data type of column '{column}' "
                            f"changed from '{expected_schema[column]}' "
                            f"to '{actual_schema[column]}'."
                        ),
                        "evidence": {
                            "column": column,
                            "expected_type": expected_schema[column],
                            "actual_type": actual_schema[column],
                        },
                    }
                )

        # ---------------------------------------------------------
        # Final result
        # ---------------------------------------------------------
        if findings:
            status = "DRIFT_DETECTED"
        else:
            status = "STABLE"

        return {
            "agent": self.agent_name,
            "status": status,
            "expected_column_count": len(expected_columns),
            "actual_column_count": len(actual_columns),
            "added_columns": added_columns,
            "removed_columns": removed_columns,
            "finding_count": len(findings),
            "findings": findings,
        }

    # -------------------------------------------------------------
    # Data-type normalization
    # -------------------------------------------------------------
    @staticmethod
    def _normalize_type(data_type: str) -> str:
        """
        Normalize common representations of data types.

        This prevents harmless naming differences such as
        'int' vs 'integer' from being treated as schema drift.
        """

        normalized = data_type.strip().lower()

        aliases = {
            "int": "integer",
            "int32": "integer",
            "int64": "integer",
            "bigint": "integer",
            "float32": "float",
            "float64": "float",
            "double": "float",
            "varchar": "string",
            "text": "string",
            "str": "string",
            "bool": "boolean",
            "datetime64": "datetime",
            "timestamp": "datetime",
        }

        return aliases.get(normalized, normalized)