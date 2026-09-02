"""The structured requirement-analysis schema.

This is the single contract used in two places: it is the schema the AI
provider must fill in (see app.ai.base.AIProvider.complete_structured), and
it is the shape persisted and returned by the API. There is deliberately one
definition, not a separate "AI schema" and "API schema" kept in sync by hand.

All models forbid extra fields: AI output is only accepted if it matches
this schema exactly, not "close enough".
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Impact = Literal["LOW", "MEDIUM", "HIGH"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FunctionalRequirementItem(StrictModel):
    id: str = Field(pattern=r"^FR-\d{3}$")
    description: str


class NonFunctionalRequirementItem(StrictModel):
    id: str = Field(pattern=r"^NFR-\d{3}$")
    description: str


class AmbiguityItem(StrictModel):
    id: str = Field(pattern=r"^AMB-\d{3}$")
    description: str
    why_it_matters: str
    impact: Impact
    information_needed: str


class AssumptionItem(StrictModel):
    id: str = Field(pattern=r"^ASM-\d{3}$")
    description: str
    reason: str
    impact: str


class ConstraintItem(StrictModel):
    id: str = Field(pattern=r"^CON-\d{3}$")
    description: str


class SuccessCriterionItem(StrictModel):
    id: str = Field(pattern=r"^SC-\d{3}$")
    description: str


class EngineeringConcernItem(StrictModel):
    id: str = Field(pattern=r"^ENG-\d{3}$")
    description: str


class RequirementAnalysisResult(StrictModel):
    summary: str
    functional_requirements: list[FunctionalRequirementItem]
    non_functional_requirements: list[NonFunctionalRequirementItem]
    ambiguities: list[AmbiguityItem]
    assumptions: list[AssumptionItem]
    constraints: list[ConstraintItem]
    success_criteria: list[SuccessCriterionItem]
    engineering_concerns: list[EngineeringConcernItem]
