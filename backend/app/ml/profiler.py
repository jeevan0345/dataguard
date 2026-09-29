"""
DataGuard ML Profiler
Computes statistical summaries of dataset columns using pure Python and NumPy.
Pandas is intentionally NOT used.
"""

from typing import Any
import numpy as np


class DatasetProfiler:
    """
    Computes statistical profiles for tabular datasets (list of dicts)
    without using pandas.
    """

    @staticmethod
    def profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
        if not rows:
            return {"row_count": 0, "columns": {}}

        row_count = len(rows)
        columns = list(rows[0].keys())
        profiles: dict[str, Any] = {}

        for col in columns:
            raw_values = [row.get(col) for row in rows]
            valid_values = [
                v for v in raw_values
                if v is not None and str(v).strip() != ""
            ]
            missing_count = row_count - len(valid_values)
            missing_percentage = round((missing_count / row_count) * 100, 2)

            numeric_values: list[float] = []
            for v in valid_values:
                try:
                    val_float = float(v)
                    if not (np.isnan(val_float) or np.isinf(val_float)):
                        numeric_values.append(val_float)
                except (ValueError, TypeError):
                    pass

            is_numeric = len(numeric_values) == len(valid_values) and len(valid_values) > 0

            if is_numeric:
                arr = np.array(numeric_values, dtype=np.float64)
                mean = float(np.mean(arr))
                std = float(np.std(arr))
                min_val = float(np.min(arr))
                max_val = float(np.max(arr))
                q25 = float(np.percentile(arr, 25))
                median = float(np.median(arr))
                q75 = float(np.percentile(arr, 75))
                iqr = q75 - q25

                profiles[col] = {
                    "data_type": "numeric",
                    "total_count": row_count,
                    "valid_count": len(valid_values),
                    "missing_count": missing_count,
                    "missing_percentage": missing_percentage,
                    "mean": round(mean, 4),
                    "std": round(std, 4),
                    "min": round(min_val, 4),
                    "max": round(max_val, 4),
                    "q25": round(q25, 4),
                    "median": round(median, 4),
                    "q75": round(q75, 4),
                    "iqr": round(iqr, 4),
                }
            else:
                str_values = [str(v) for v in valid_values]
                unique_values = set(str_values)
                profiles[col] = {
                    "data_type": "categorical",
                    "total_count": row_count,
                    "valid_count": len(valid_values),
                    "missing_count": missing_count,
                    "missing_percentage": missing_percentage,
                    "unique_count": len(unique_values),
                }

        return {
            "row_count": row_count,
            "column_count": len(columns),
            "columns": profiles,
        }
