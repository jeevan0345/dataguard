import pandas as pd


class DatasetProfiler:

    @staticmethod
    def profile(df: pd.DataFrame):

        profile = {

            "rows": len(df),

            "columns": len(df.columns),

            "column_names": list(df.columns),

            "data_types": df.dtypes.astype(str).to_dict(),

            "missing_values": df.isnull().sum().to_dict(),

            "duplicate_rows": int(df.duplicated().sum()),

          "memory_usage_mb": float(
    round(
        df.memory_usage(deep=True).sum() / (1024 * 1024),
        2
    )
),

            "numeric_columns": list(
                df.select_dtypes(include="number").columns
            ),

            "categorical_columns": list(
                df.select_dtypes(include="object").columns
            )

        }

        return profile