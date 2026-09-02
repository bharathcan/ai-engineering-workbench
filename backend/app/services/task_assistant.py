from app.ai.base import AIProvider
from app.ai.prompts import TASK_ASSIST_SYSTEM_PROMPT
from app.schemas.ai_recommendation import AIRecommendation


class TaskAssistant:
    """Requests an AI recommendation for one specific, already-approved
    task, given an already-built prompt (app.ai.prompts.build_task_assist_
    user_prompt). Never modifies the repository, executes anything, or
    decides a task is complete — it only produces a recommendation for
    engineer review. See docs/api-design.md 'No Automatic Code Execution'.
    """

    def __init__(self, ai_provider: AIProvider):
        self._ai_provider = ai_provider

    def assist(self, user_prompt: str) -> AIRecommendation:
        return self._ai_provider.complete_structured(
            system_prompt=TASK_ASSIST_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=AIRecommendation,
        )
