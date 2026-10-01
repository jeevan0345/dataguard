from typing import Any


class DatasetValidator:
    """
    Pandas-free dataset validator for tabular data.
    """

    @staticmethod
    def validate(data: list[dict[str, Any]] | Any) -> dict[str, Any]:
        if not data:
            return {
                "total_rows": 0,
                "total_columns": 0,
                "missing_values": 0,
                "duplicate_rows": 0,
                "empty_columns": [],
                "quality_score": 100.0,
                "is_valid": True,
            }

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
        total_cells = total_rows * total_cols if total_cols > 0 else 1

        missing_count = 0
        empty_columns: list[str] = []

        for col in columns:
            col_missing = sum(1 for r in rows if r.get(col) is None or str(r.get(col)).strip() == "")
            missing_count += col_missing
            if col_missing == total_rows and total_rows > 0:
                empty_columns.append(col)

        row_tuples = [tuple(r.get(col) for col in columns) for r in rows]
        duplicate_rows = len(row_tuples) - len(set(row_tuples))

        completeness_pct = (1.0 - (missing_count / total_cells)) * 100.0 if total_cells > 0 else 100.0
        uniqueness_pct = (1.0 - (duplicate_rows / total_rows)) * 100.0 if total_rows > 0 else 100.0
        quality_score = round(max(0.0, min(100.0, 0.6 * completeness_pct + 0.4 * uniqueness_pct)), 2)

        is_valid = (
            missing_count == 0
            and duplicate_rows == 0
            and len(empty_columns) == 0
        )

        return {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "missing_values": missing_count,
            "duplicate_rows": duplicate_rows,
            "empty_columns": empty_columns,
            "quality_score": quality_score,
            "is_valid": is_valid,
        }