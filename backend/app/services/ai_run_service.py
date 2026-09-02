import time
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.ai.base import AIProvider
from app.ai.prompts import build_task_assist_user_prompt
from app.core.exceptions import (
    AIProviderError,
    AIRunNotFoundError,
    InvalidAIResponseError,
    TaskNotApprovedError,
    TaskNotFoundError,
)
from app.models.engineering_plan import AIRun, EngineeringTask
from app.repositories import ai_run_repository, engineering_plan_repository
from app.schemas.ai_run import AIRunResponse
from app.services.ai_run_mapper import to_ai_run_response
from app.services.task_assistant import TaskAssistant

REQUIRED_TASK_STATUS = "APPROVED"

# AIRun.error is persisted and later returned to the client via GET
# .../tasks/{id} (which embeds AI-run history) — so it must never contain
# the raw provider exception text, which could echo request/response
# internals from a third-party SDK. The real exception is still logged
# server-side by the route layer (never returned to the client); only a
# fixed, safe classification is stored/exposed here. This is a deliberate
# simplification rather than attempting redaction of arbitrary error text,
# which would be unreliable — see docs/validation/PHASE-5-SECURITY-REVIEW.md.
GENERIC_PROVIDER_ERROR_MESSAGE = "The AI provider request failed."
GENERIC_INVALID_RESPONSE_MESSAGE = "The AI provider's response failed schema validation."


def request_ai_assistance(
    db: Session,
    task_id: str,
    assistance_type: str,
    instructions: str | None,
    ai_provider_factory: Callable[[], AIProvider],
) -> AIRunResponse:
    task = _get_task_or_raise(db, task_id)
    if task.status != REQUIRED_TASK_STATUS:
        raise TaskNotApprovedError(task_id, task.status)

    revised_from_ai_run_id, prior_feedback = _revision_context(db, task)

    user_prompt = build_task_assist_user_prompt(
        task_id=task.public_id,
        title=task.title,
        description=task.description,
        requirement_refs=task.requirement_refs,
        acceptance_criteria=task.acceptance_criteria,
        risks=[r.get("description", "") for r in task.risks],
        assumptions=task.plan.assumptions,
        assistance_type=assistance_type,
        instructions=instructions,
        prior_feedback=prior_feedback,
    )

    ai_provider = ai_provider_factory()
    start = time.monotonic()
    try:
        recommendation = TaskAssistant(ai_provider).assist(user_prompt)
    except AIProviderError:
        ai_run_repository.save_failed_run(
            db,
            task,
            provider=ai_provider.provider_name,
            model=ai_provider.model_name,
            assistance_type=assistance_type,
            instructions=instructions,
            prompt=user_prompt,
            error=GENERIC_PROVIDER_ERROR_MESSAGE,
            duration_ms=_elapsed_ms(start),
            revised_from_ai_run_id=revised_from_ai_run_id,
        )
        raise
    except InvalidAIResponseError:
        ai_run_repository.save_failed_run(
            db,
            task,
            provider=ai_provider.provider_name,
            model=ai_provider.model_name,
            assistance_type=assistance_type,
            instructions=instructions,
            prompt=user_prompt,
            error=GENERIC_INVALID_RESPONSE_MESSAGE,
            duration_ms=_elapsed_ms(start),
            revised_from_ai_run_id=revised_from_ai_run_id,
        )
        raise

    run = ai_run_repository.save_completed_run(
        db,
        task,
        provider=ai_provider.provider_name,
        model=ai_provider.model_name,
        assistance_type=assistance_type,
        instructions=instructions,
        prompt=user_prompt,
        recommendation=recommendation,
        duration_ms=_elapsed_ms(start),
        revised_from_ai_run_id=revised_from_ai_run_id,
    )
    return to_ai_run_response(run)


def decide_ai_run(
    db: Session, ai_run_id: str, decision: str, rationale: str | None, changes: str | None
) -> AIRunResponse:
    run = _get_ai_run_or_raise(db, ai_run_id)
    ai_run_repository.save_ai_run_decision(db, run, decision, rationale, changes)
    db.refresh(run)
    return to_ai_run_response(run)


def _revision_context(db: Session, task: EngineeringTask) -> tuple[int | None, str | None]:
    """If the task's most recent AI run was sent back with MODIFY, this new
    request is a revision of it: link revised_from_ai_run_id and fold the
    engineer's feedback into the prompt. Otherwise this is an independent
    run (fresh request, or one following ACCEPT/REJECT)."""
    latest_run = ai_run_repository.get_latest_ai_run_for_task(db, task)
    if latest_run is None or not latest_run.decisions:
        return None, None

    latest_decision = latest_run.decisions[-1]
    if latest_decision.decision != "MODIFY":
        return None, None

    feedback_parts = []
    if latest_decision.rationale:
        feedback_parts.append(f"Rationale: {latest_decision.rationale}")
    if latest_decision.changes:
        feedback_parts.append(f"Requested changes: {latest_decision.changes}")
    return latest_run.id, " ".join(feedback_parts) or None


def _elapsed_ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


def _get_task_or_raise(db: Session, task_id: str) -> EngineeringTask:
    task = engineering_plan_repository.get_task_by_public_id(db, task_id)
    if task is None:
        raise TaskNotFoundError(task_id)
    return task


def _get_ai_run_or_raise(db: Session, ai_run_id: str) -> AIRun:
    run = ai_run_repository.get_ai_run_by_public_id(db, ai_run_id)
    if run is None:
        raise AIRunNotFoundError(ai_run_id)
    return run
