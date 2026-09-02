from datetime import datetime
from typing import Literal

from pydantic import BaseModel, model_validator

from app.schemas.ai_run import AIRunResponse
from app.schemas.decision import EngineerDecisionResponse
from app.schemas.task_decomposition import AIAssistanceType, RiskItem, TaskType


class TaskResponse(BaseModel):
    id: str
    plan_id: str
    title: str
    description: str
    type: TaskType
    requirement_refs: list[str]
    dependencies: list[str]
    sequence: int
    acceptance_criteria: list[str]
    ai_assistance_type: AIAssistanceType
    risks: list[RiskItem]
    status: str
    review_status: str
    decisions: list[EngineerDecisionResponse]
    ai_runs: list[AIRunResponse]
    created_at: datetime


class EngineeringPlanResponse(BaseModel):
    id: str
    requirement_id: str
    requirement_analysis_id: str
    status: Literal["GENERATED", "BLOCKED"]
    blocked_reason: str | None
    summary: str
    tasks: list[TaskResponse]
    assumptions: list[str]
    unresolved_ambiguities: list[str]
    risks: list[RiskItem]
    review_status: str
    created_at: datetime


class TaskDecisionRequest(BaseModel):
    decision: Literal["ACCEPT", "MODIFY", "REJECT"]
    rationale: str | None = None
    changes: str | None = None

    @model_validator(mode="after")
    def rationale_required_for_modify_or_reject(self) -> "TaskDecisionRequest":
        if self.decision in ("MODIFY", "REJECT") and not (self.rationale or "").strip():
            raise ValueError(f"rationale is required when decision is {self.decision}.")
        if self.decision == "MODIFY" and not (self.changes or "").strip():
            raise ValueError("changes is required when decision is MODIFY.")
        return self
