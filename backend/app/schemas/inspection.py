from typing import Any

from pydantic import BaseModel, Field


class InspectionRequest(BaseModel):
    """
    Request payload for running a DataGuard dataset inspection.
    """

    dataset_path: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description=(
            "Dataset path relative to the DataGuard "
            "datasets directory."
        ),
    )

    expected_schema: dict[str, str] | None = Field(
        default=None,
        description=(
            "Expected schema used for schema drift detection."
        ),
    )


class InspectionFindingResponse(BaseModel):
    """
    API representation of one Inspector Agent finding.
    """

    type: str

    severity: str

    message: str

    evidence: dict[str, Any]


class DataQualityInspectionResponse(BaseModel):
    """
    Data Quality Agent result.
    """

    agent: str

    status: str

    row_count: int

    finding_count: int

    findings: list[InspectionFindingResponse]


class SchemaDriftInspectionResponse(BaseModel):
    """
    Schema Drift Agent result.
    """

    agent: str

    status: str

    expected_column_count: int

    actual_column_count: int

    added_columns: list[str]

    removed_columns: list[str]

    finding_count: int

    findings: list[InspectionFindingResponse]


class InspectorResultResponse(BaseModel):
    """
    Unified Inspector Agent result.
    """

    agent: str

    status: str

    highest_severity: str | None

    finding_count: int

    findings: list[InspectionFindingResponse]

    data_quality: DataQualityInspectionResponse

    schema_drift: SchemaDriftInspectionResponse | None

    ml_analysis: dict[str, Any] | None = None


class EvidenceItemResponse(BaseModel):
    evidence_id: str
    finding_type: str
    severity: str
    message: str
    evidence: dict[str, Any]


class EvidenceEngineResponse(BaseModel):
    engine: str
    status: str
    finding_count: int
    evidence_count: int
    evidence: list[EvidenceItemResponse]


class RootCauseCandidateResponse(BaseModel):
    cause: str
    confidence: float
    evidence: list[str]
    affected_area: str
    explanation: str


class RootCauseResponse(BaseModel):
    run_id: str
    finding_count: int
    primary_cause: str | None = None
    overall_confidence: float
    summary: str
    candidates: list[RootCauseCandidateResponse]


class InspectionPersistenceResponse(BaseModel):
    """
    Persistence information returned after an inspection
    is successfully saved into PostgreSQL.
    """

    saved: bool

    inspection_id: str

    finding_count: int


class InspectionResponse(BaseModel):
    """
    Complete API response for a DataGuard inspection.

    Includes:
    - dataset information
    - inferred schema
    - Inspector Agent result
    - PostgreSQL inspection ID
    - persistence status
    - Evidence Engine results
    - Root Cause Analysis
    """

    dataset_path: str | None

    row_count: int

    column_count: int

    actual_schema: dict[str, str]

    inspection: InspectorResultResponse

    inspection_id: str

    persistence: InspectionPersistenceResponse

    evidence: EvidenceEngineResponse | None = None

    root_cause: RootCauseResponse | None = None