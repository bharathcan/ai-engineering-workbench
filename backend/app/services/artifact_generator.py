from app.ai.base import AIProvider
from app.ai.prompts import ARTIFACT_GENERATION_SYSTEM_PROMPT
from app.schemas.artifact_generation import ArtifactGenerationResult


class ArtifactGenerator:
    """Produces draft artifact content (path + content + type) from an
    already-ACCEPTed AI recommendation, given an already-built prompt
    (app.ai.prompts.build_artifact_generation_user_prompt). Never writes to
    disk itself — see app.services.artifact_service, which validates every
    proposed path (app.utils.safe_path) before anything is persisted or
    written."""

    def __init__(self, ai_provider: AIProvider):
        self._ai_provider = ai_provider

    def generate(self, user_prompt: str) -> ArtifactGenerationResult:
        return self._ai_provider.complete_structured(
            system_prompt=ARTIFACT_GENERATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ArtifactGenerationResult,
        )
