from typing import Any
import sys


class DatasetProfiler:
    """
    Pandas-free dataset profiler for tabular data (list of row dicts).
    """

    @staticmethod
    def profile(data: list[dict[str, Any]] | Any) -> dict[str, Any]:
        if not data:
            return {
                "rows": 0,
                "columns": 0,
                "column_names": [],
                "data_types": {},
                "missing_values": {},
                "duplicate_rows": 0,
                "memory_usage_mb": 0.0,
                "numeric_columns": [],
                "categorical_columns": [],
            }

        # If data is list of dicts
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            rows = data
            columns = list(rows[0].keys())
        elif hasattr(data, "to_dict"):
            rows = data.to_dict("records")
            columns = list(rows[0].keys()) if rows else []
        else:
            rows = list(data)
            columns = []

        total_rows = len(rows)
        total_cols = len(columns)

        data_types: dict[str, str] = {}
        missing_values: dict[str, int] = {}
        numeric_columns: list[str] = []
        categorical_columns: list[str] = []

        for col in columns:
            raw_vals = [r.get(col) for r in rows]
            missing_count = sum(1 for v in raw_vals if v is None or str(v).strip() == "")
            missing_values[col] = missing_count

            # check numeric
            valid_vals = [v for v in raw_vals if v is not None and str(v).strip() != ""]
            is_num = False
            if valid_vals:
                try:
                    for v in valid_vals:
                        float(v)
                    is_num = True
                except (ValueError, TypeError):
                    is_num = False

            if is_num:
                data_types[col] = "float64"
                numeric_columns.append(col)
            else:
                data_types[col] = "object"
                categorical_columns.append(col)

        # Duplicate rows
        row_tuples = [tuple(r.get(col) for col in columns) for r in rows]
        duplicate_rows = len(row_tuples) - len(set(row_tuples))

        # Memory usage estimate
        approx_bytes = sys.getsizeof(rows) + sum(sys.getsizeof(r) for r in rows)
        memory_usage_mb = round(approx_bytes / (1024 * 1024), 2)

        return {
            "rows": total_rows,
            "columns": total_cols,
            "column_names": columns,
            "data_types": data_types,
            "missing_values": missing_values,
            "duplicate_rows": duplicate_rows,
            "memory_usage_mb": memory_usage_mb,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
        }