from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator

from app.schemas.artifact_generation import ArtifactType
from app.schemas.decision import EngineerDecisionResponse


class ArtifactResponse(BaseModel):
    id: str
    task_id: str
    ai_run_id: str
    artifact_type: ArtifactType
    path: str
    content: str
    description: str
    status: Literal["PENDING_REVIEW", "APPROVED", "NEEDS_REVISION", "REJECTED"]
    version: int
    supersedes_artifact_id: str | None
    # Unified diff against the version this one supersedes, or against an
    # empty file if this is version 1 — computed at read time, not stored.
    diff: str | None
    decisions: list[EngineerDecisionResponse]
    created_at: datetime


class ArtifactDecisionRequest(BaseModel):
    decision: Literal["ACCEPT", "MODIFY", "REJECT"]
    rationale: str | None = None
    changes: str | None = None

    @model_validator(mode="after")
    def rationale_required_for_modify_or_reject(self) -> "ArtifactDecisionRequest":
        if self.decision in ("MODIFY", "REJECT") and not (self.rationale or "").strip():
            raise ValueError(f"rationale is required when decision is {self.decision}.")
        if self.decision == "MODIFY" and not (self.changes or "").strip():
            raise ValueError("changes is required when decision is MODIFY.")
        return self
