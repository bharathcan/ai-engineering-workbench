"""The structured task-decomposition schema — the AI's output contract for
POST /api/v1/requirements/{id}/tasks.

Task ids and dependencies here are *plan-local*: the AI numbers tasks
TASK-001, TASK-002, ... within this one response, and dependencies reference
those local ids. Persistence remaps them to globally unique public ids
(app.services.task_decomposer._persist_plan) — the AI has no way to know a
task's eventual database id in advance, so asking it to produce local,
self-consistent ids and validating referential integrity ourselves is more
robust than asking it to guess global ids.
"""

from typing import Literal

from pydantic import Field

from app.schemas.requirement_analysis import Impact, StrictModel

TaskType = Literal[
    "ARCHITECTURE",
    "API",
    "DATABASE",
    "BACKEND",
    "FRONTEND",
    "TESTING",
    "SECURITY",
    "PERFORMANCE",
    "DOCUMENTATION",
    "INFRASTRUCTURE",
    "VALIDATION",
]

AIAssistanceType = Literal[
    "DESIGN",
    "CODE_GENERATION",
    "DEBUGGING",
    "REFACTORING",
    "TEST_GENERATION",
    "DOCUMENTATION",
    "SECURITY_REVIEW",
    "PERFORMANCE_REVIEW",
    "NONE",
]


class RiskItem(StrictModel):
    id: str = Field(pattern=r"^RISK-\d{3}$")
    description: str
    impact: Impact


class TaskPlanItem(StrictModel):
    id: str = Field(pattern=r"^TASK-\d{3}$")
    title: str
    description: str
    type: TaskType
    requirement_refs: list[str]
    dependencies: list[str] = Field(default_factory=list)
    sequence: int
    acceptance_criteria: list[str]
    ai_assistance_type: AIAssistanceType
    risks: list[RiskItem] = Field(default_factory=list)


class TaskDecompositionResult(StrictModel):
    summary: str
    tasks: list[TaskPlanItem]
    assumptions: list[str] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)
