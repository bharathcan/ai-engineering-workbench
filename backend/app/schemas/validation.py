from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ValidationType = Literal[
    "UNIT_TEST",
    "INTEGRATION_TEST",
    "API_CONTRACT",
    "STATIC_ANALYSIS",
    "SECURITY",
    "PERFORMANCE",
    "BUILD",
]

ValidationStatus = Literal["PENDING", "RUNNING", "PASSED", "FAILED", "NOT_VALIDATED"]


class ValidationRequest(BaseModel):
    validation_type: ValidationType


class ValidationResponse(BaseModel):
    id: str
    artifact_id: str
    task_id: str
    validation_type: ValidationType
    command: str
    status: ValidationStatus
    output: str
    evidence: str
    error: str | None
    duration_ms: int
    metadata: dict
    created_at: datetime
