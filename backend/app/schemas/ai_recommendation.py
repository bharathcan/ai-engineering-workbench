"""The structured AI-recommendation schema — the AI's output contract for
POST /api/v1/tasks/{task_id}/ai-assist.

This is a recommendation, not an implementation: proposed_changes and
tests_to_add are plain descriptive strings, not diffs or file contents. The
AI never writes to the repository — see docs/api-design.md "No Automatic
Code Execution".
"""

from typing import Literal

from pydantic import Field

from app.schemas.requirement_analysis import StrictModel

Confidence = Literal["LOW", "MEDIUM", "HIGH"]


class AIRecommendation(StrictModel):
    summary: str
    approach: str
    files_to_change: list[str] = Field(default_factory=list)
    proposed_changes: list[str] = Field(default_factory=list)
    tests_to_add: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: Confidence
