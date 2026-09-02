from datetime import datetime

from pydantic import BaseModel, field_validator

from app.schemas.requirement_analysis import RequirementAnalysisResult

MAX_REQUIREMENT_LENGTH = 10_000


class RequirementCreateRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def text_must_be_meaningful(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Requirement text must not be empty.")
        if len(stripped) > MAX_REQUIREMENT_LENGTH:
            raise ValueError(
                f"Requirement text must not exceed {MAX_REQUIREMENT_LENGTH} characters."
            )
        return stripped


class RequirementClarifyRequest(BaseModel):
    clarifications: str

    @field_validator("clarifications")
    @classmethod
    def clarifications_must_be_meaningful(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Clarifications must not be empty.")
        if len(stripped) > MAX_REQUIREMENT_LENGTH:
            raise ValueError(
                f"Clarifications must not exceed {MAX_REQUIREMENT_LENGTH} characters."
            )
        return stripped


class RequirementResponse(BaseModel):
    id: str
    text: str
    status: str
    created_at: datetime
    latest_analysis: RequirementAnalysisResult | None = None
