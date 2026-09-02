from app.ai.base import AIProvider
from app.ai.prompts import (
    REQUIREMENT_ANALYSIS_SYSTEM_PROMPT,
    build_requirement_analysis_user_prompt,
    build_requirement_clarification_user_prompt,
)
from app.schemas.requirement_analysis import RequirementAnalysisResult


class RequirementAnalyzer:
    """Understands a raw requirement. Does not decompose it into tasks and
    does not generate implementation code — see docs/ENGINEERING_WORKFLOW.md
    for where those responsibilities live instead."""

    def __init__(self, ai_provider: AIProvider):
        self._ai_provider = ai_provider

    def analyze(self, raw_text: str) -> RequirementAnalysisResult:
        return self._ai_provider.complete_structured(
            system_prompt=REQUIREMENT_ANALYSIS_SYSTEM_PROMPT,
            user_prompt=build_requirement_analysis_user_prompt(raw_text),
            response_model=RequirementAnalysisResult,
        )

    def analyze_with_context(
        self, raw_text: str, clarifications: str, prior_analysis_summary: str
    ) -> RequirementAnalysisResult:
        """Re-analyze after clarifications, preserving prior analysis structure."""
        return self._ai_provider.complete_structured(
            system_prompt=REQUIREMENT_ANALYSIS_SYSTEM_PROMPT,
            user_prompt=build_requirement_clarification_user_prompt(
                raw_text, clarifications, prior_analysis_summary
            ),
            response_model=RequirementAnalysisResult,
        )
