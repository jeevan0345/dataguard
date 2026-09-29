from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ETLRunCreate(BaseModel):
    """
    Data required to create a new ETL run.
    """

    pipeline_id: str
    dataset_id: Optional[str] = None

    started_at: datetime

    status: str = "RUNNING"

    rows_input: Optional[int] = None
    rows_output: Optional[int] = None

    duration_ms: Optional[float] = None

    error_message: Optional[str] = None

    checkpoint: Optional[str] = None


class ETLRunUpdate(BaseModel):
    """
    Data that can be updated when an ETL run progresses or completes.
    """

    completed_at: Optional[datetime] = None

    status: Optional[str] = None

    rows_input: Optional[int] = None
    rows_output: Optional[int] = None

    duration_ms: Optional[float] = None

    error_message: Optional[str] = None

    checkpoint: Optional[str] = None


class ETLRunResponse(BaseModel):
    """
    API response returned for an ETL run.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    pipeline_id: str
    dataset_id: Optional[str]

    started_at: datetime
    completed_at: Optional[datetime]

    status: str

    rows_input: Optional[int]
    rows_output: Optional[int]

    duration_ms: Optional[float]

    error_message: Optional[str]

    checkpoint: Optional[str]

    created_at: datetime
    updated_at: datetime
    is_active: bool