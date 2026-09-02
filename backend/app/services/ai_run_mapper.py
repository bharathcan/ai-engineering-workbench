from app.models.engineering_plan import AIRun
from app.schemas.ai_recommendation import AIRecommendation
from app.schemas.ai_run import AIRunResponse
from app.services.decision_mapper import to_decision_response


def to_ai_run_response(run: AIRun) -> AIRunResponse:
    """Shared by ai_run_service (the ai-assist/decision endpoints) and
    engineering_plan_service (which embeds a task's AI run history in
    GET .../tasks responses) so the two don't drift."""
    return AIRunResponse(
        id=run.public_id,
        task_id=run.task.public_id,
        provider=run.provider,
        model=run.model,
        assistance_type=run.assistance_type,
        instructions=run.instructions,
        prompt=run.prompt,
        status=run.status,
        response=AIRecommendation.model_validate(run.response) if run.response else None,
        error=run.error,
        duration_ms=run.duration_ms,
        revised_from_ai_run_id=(
            f"AI-RUN-{run.revised_from_ai_run_id:03d}" if run.revised_from_ai_run_id else None
        ),
        decisions=[to_decision_response(d) for d in run.decisions],
        created_at=run.created_at,
    )
