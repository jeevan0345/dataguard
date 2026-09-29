from datetime import datetime
from typing import Any


class SchemaInference:
    """
    Infers the logical data type of each dataset column.

    Supported types:
    - boolean
    - integer
    - float
    - datetime
    - string

    Empty and whitespace-only values are ignored during inference.

    Identifier-like columns are treated as strings even when their
    values contain only digits. This prevents IDs such as order_id
    and customer_id from being incorrectly classified as integers.
    """

    TYPE_BOOLEAN = "boolean"
    TYPE_INTEGER = "integer"
    TYPE_FLOAT = "float"
    TYPE_DATETIME = "datetime"
    TYPE_STRING = "string"

    # Common identifier naming patterns.
    IDENTIFIER_NAMES = {
        "id",
        "order_id",
        "customer_id",
        "product_id",
        "seller_id",
        "user_id",
        "employee_id",
        "customer_number",
        "account_id",
        "transaction_id",
        "invoice_id",
    }

    @classmethod
    def infer_schema(
        cls,
        rows: list[dict[str, Any]]
    ) -> dict[str, str]:
        """
        Infer the logical schema of the supplied dataset.
        """

        if not rows:
            return {}

        columns = cls._get_columns(rows)

        schema: dict[str, str] = {}

        for column in columns:
            values = [
                row.get(column)
                for row in rows
                if cls._is_meaningful_value(row.get(column))
            ]

            schema[column] = cls._infer_column_type(
                column=column,
                values=values,
            )

        return schema

    @staticmethod
    def _get_columns(
        rows: list[dict[str, Any]]
    ) -> list[str]:
        """
        Collect all unique columns while preserving their order.
        """

        columns: list[str] = []
        seen: set[str] = set()

        for row in rows:
            for column in row.keys():
                if column not in seen:
                    seen.add(column)
                    columns.append(column)

        return columns

    @classmethod
    def _infer_column_type(
        cls,
        column: str,
        values: list[Any]
    ) -> str:
        """
        Infer the most appropriate logical type for a column.
        """

        if not values:
            return cls.TYPE_STRING

        # -----------------------------------------------------
        # Identifier protection
        # -----------------------------------------------------
        # IDs should remain strings even when their values are
        # numeric-looking, e.g. "1001".
        if cls._is_identifier_column(column):
            return cls.TYPE_STRING

        # -----------------------------------------------------
        # Boolean
        # -----------------------------------------------------
        if all(cls._is_boolean(value) for value in values):
            return cls.TYPE_BOOLEAN

        # -----------------------------------------------------
        # Integer
        # -----------------------------------------------------
        if all(cls._is_integer(value) for value in values):
            return cls.TYPE_INTEGER

        # -----------------------------------------------------
        # Float
        # -----------------------------------------------------
        if all(cls._is_float(value) for value in values):
            return cls.TYPE_FLOAT

        # -----------------------------------------------------
        # Datetime
        # -----------------------------------------------------
        if all(cls._is_datetime(value) for value in values):
            return cls.TYPE_DATETIME

        # -----------------------------------------------------
        # Default
        # -----------------------------------------------------
        return cls.TYPE_STRING

    @classmethod
    def _is_identifier_column(
        cls,
        column: str
    ) -> bool:
        """
        Determine whether a column represents an identifier.
        """

        normalized = column.strip().lower()

        if normalized in cls.IDENTIFIER_NAMES:
            return True

        # Handles names such as:
        # order_id
        # product_id
        # seller_id
        # customer_id
        # user_id
        if normalized.endswith("_id"):
            return True

        return False

    @staticmethod
    def _is_meaningful_value(
        value: Any
    ) -> bool:
        """
        Determine whether a value should participate in
        schema inference.

        None, empty strings and whitespace-only strings are
        ignored.
        """

        if value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        return True

    @staticmethod
    def _is_boolean(
        value: Any
    ) -> bool:
        """
        Check whether a value represents a boolean.
        """

        if isinstance(value, bool):
            return True

        if not isinstance(value, str):
            return False

        return value.strip().lower() in {
            "true",
            "false",
            "yes",
            "no",
        }

    @staticmethod
    def _is_integer(
        value: Any
    ) -> bool:
        """
        Check whether a value represents an integer.
        """

        if isinstance(value, bool):
            return False

        if isinstance(value, int):
            return True

        if not isinstance(value, str):
            return False

        value = value.strip()

        if not value:
            return False

        try:
            int(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_float(
        value: Any
    ) -> bool:
        """
        Check whether a value represents a floating-point number.
        """

        if isinstance(value, bool):
            return False

        if isinstance(value, float):
            return True

        if isinstance(value, int):
            return True

        if not isinstance(value, str):
            return False

        value = value.strip()

        if not value:
            return False

        try:
            float(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_datetime(
        value: Any
    ) -> bool:
        """
        Check whether a value represents a supported
        date or datetime format.
        """

        if isinstance(value, datetime):
            return True

        if not isinstance(value, str):
            return False

        value = value.strip()

        if not value:
            return False

        datetime_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
        ]

        for date_format in datetime_formats:
            try:
                datetime.strptime(
                    value,
                    date_format
                )
                return True
            except ValueError:
                continue

        return False