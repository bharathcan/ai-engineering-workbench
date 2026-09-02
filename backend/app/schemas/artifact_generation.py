"""The structured artifact-generation schema — the AI's output contract for
POST /api/v1/ai-runs/{ai_run_id}/artifacts.

Unlike app.schemas.ai_recommendation.AIRecommendation (Phase 5, which is
proposal text only), this schema's `content` fields are real file content —
this is the one place in the workbench where the AI produces something
closer to actual code. It is still never written anywhere without engineer
approval — see docs/api-design.md "Controlled File Writes" and "Artifact
Lifecycle".
"""

from typing import Literal

from pydantic import Field

from app.schemas.requirement_analysis import StrictModel

ArtifactType = Literal[
    "SOURCE_CODE",
    "API_CONTRACT",
    "DATABASE_SCHEMA",
    "TEST",
    "DOCUMENTATION",
    "CONFIGURATION",
    "ARCHITECTURE",
]


class ArtifactDraftItem(StrictModel):
    artifact_type: ArtifactType
    path: str = Field(min_length=1, max_length=500)
    content: str
    description: str


class ArtifactGenerationResult(StrictModel):
    artifacts: list[ArtifactDraftItem]
