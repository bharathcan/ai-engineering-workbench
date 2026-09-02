from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator

from app.schemas.ai_recommendation import AIRecommendation
from app.schemas.decision import EngineerDecisionResponse

# Deliberately not the same Literal as app.schemas.task_decomposition.AIAssistanceType:
# that one includes "NONE" (a task may need no AI assistance at all), which is not a
# meaningful value to *request* assistance with.
AIAssistRequestType = Literal[
    "DESIGN",
    "CODE_GENERATION",
    "DEBUGGING",
    "REFACTORING",
    "TEST_GENERATION",
    "DOCUMENTATION",
    "SECURITY_REVIEW",
    "PERFORMANCE_REVIEW",
]


class AIAssistRequest(BaseModel):
    assistance_type: AIAssistRequestType
    instructions: str | None = None


class AIRunResponse(BaseModel):
    id: str
    task_id: str
    provider: str
    model: str
    assistance_type: AIAssistRequestType
    instructions: str | None
    status: Literal["COMPLETED", "FAILED"]
    response: AIRecommendation | None
    error: str | None
    duration_ms: int
    revised_from_ai_run_id: str | None
    decisions: list[EngineerDecisionResponse]
    created_at: datetime


class AIRunDecisionRequest(BaseModel):
    decision: Literal["ACCEPT", "MODIFY", "REJECT"]
    rationale: str | None = None
    changes: str | None = None

    @model_validator(mode="after")
    def rationale_required_for_modify_or_reject(self) -> "AIRunDecisionRequest":
        if self.decision in ("MODIFY", "REJECT") and not (self.rationale or "").strip():
            raise ValueError(f"rationale is required when decision is {self.decision}.")
        if self.decision == "MODIFY" and not (self.changes or "").strip():
            raise ValueError("changes is required when decision is MODIFY.")
        return self
