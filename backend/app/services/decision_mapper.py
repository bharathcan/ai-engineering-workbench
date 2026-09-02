from app.models.engineering_plan import EngineerDecision
from app.schemas.decision import EngineerDecisionResponse


def to_decision_response(decision: EngineerDecision) -> EngineerDecisionResponse:
    """Shared by engineering_plan_service (task-plan decisions) and
    ai_run_service (AI-run decisions) so the two don't drift."""
    return EngineerDecisionResponse(
        id=decision.public_id,
        ai_run_id=f"AI-RUN-{decision.ai_run_id:03d}" if decision.ai_run_id else None,
        decision=decision.decision,
        rationale=decision.rationale,
        changes=decision.changes,
        reviewer=decision.reviewer,
        created_at=decision.created_at,
    )
