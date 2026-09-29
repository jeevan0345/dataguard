from datetime import datetime
from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DatasetRegistryBase(BaseModel):

    dataset_name: str
    dataset_type: str
    source: str
    file_path: str
    file_format: str


class DatasetRegistryCreate(DatasetRegistryBase):
    pass


class DatasetRegistryUpdate(BaseModel):

    row_count: Optional[int] = None
    column_count: Optional[int] = None
    quality_score: Optional[float] = None
    status: Optional[str] = None
    last_profiled_at: Optional[datetime] = None


class DatasetRegistryResponse(DatasetRegistryBase):

    id: Union[str, UUID]

    row_count: int = 0
    column_count: int = 0

    quality_score: float = 0.0

    status: str = "Registered"

    uploaded_at: Optional[datetime] = None
    last_profiled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)