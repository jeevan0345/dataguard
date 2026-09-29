import pandas as pd


class DatasetValidator:

    @staticmethod
    def validate(df: pd.DataFrame):

        total_cells = df.shape[0] * df.shape[1]

        missing_values = int(df.isnull().sum().sum())

        duplicate_rows = int(df.duplicated().sum())

        empty_columns = [
            column
            for column in df.columns
            if df[column].isnull().all()
        ]

        quality_score = round(
            (
                (
                    total_cells
                    - missing_values
                    - duplicate_rows
                )
                / total_cells
            )
            * 100,
            2
        )

        return {

            "total_rows": len(df),

            "total_columns": len(df.columns),

            "missing_values": missing_values,

            "duplicate_rows": duplicate_rows,

            "empty_columns": empty_columns,

            "quality_score": quality_score,

            "is_valid": (
                missing_values == 0
                and duplicate_rows == 0
                and len(empty_columns) == 0
            )

        }