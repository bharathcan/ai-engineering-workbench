from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError
from app.models.engineering_plan import AIRun, EngineerDecision, EngineeringTask
from app.schemas.ai_recommendation import AIRecommendation


def save_completed_run(
    db: Session,
    task: EngineeringTask,
    *,
    provider: str,
    model: str,
    assistance_type: str,
    instructions: str | None,
    prompt: str,
    recommendation: AIRecommendation,
    duration_ms: int,
    revised_from_ai_run_id: int | None,
) -> AIRun:
    try:
        run = AIRun(
            task_id=task.id,
            provider=provider,
            model=model,
            assistance_type=assistance_type,
            instructions=instructions,
            prompt=prompt,
            status="COMPLETED",
            response=recommendation.model_dump(),
            error=None,
            duration_ms=duration_ms,
            revised_from_ai_run_id=revised_from_ai_run_id,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to save AI run.") from exc


def save_failed_run(
    db: Session,
    task: EngineeringTask,
    *,
    provider: str,
    model: str,
    assistance_type: str,
    instructions: str | None,
    prompt: str,
    error: str,
    duration_ms: int,
    revised_from_ai_run_id: int | None,
) -> AIRun:
    try:
        run = AIRun(
            task_id=task.id,
            provider=provider,
            model=model,
            assistance_type=assistance_type,
            instructions=instructions,
            prompt=prompt,
            status="FAILED",
            response=None,
            error=error,
            duration_ms=duration_ms,
            revised_from_ai_run_id=revised_from_ai_run_id,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to save failed AI run.") from exc


def get_ai_run_by_public_id(db: Session, ai_run_id: str) -> AIRun | None:
    numeric_id = _parse_ai_run_public_id(ai_run_id)
    if numeric_id is None:
        return None
    try:
        return db.get(AIRun, numeric_id)
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load AI run.") from exc


def get_latest_ai_run_for_task(db: Session, task: EngineeringTask) -> AIRun | None:
    try:
        return (
            db.query(AIRun)
            .filter(AIRun.task_id == task.id)
            .order_by(AIRun.id.desc())
            .first()
        )
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load AI run history.") from exc


def save_ai_run_decision(
    db: Session, ai_run: AIRun, decision: str, rationale: str | None, changes: str | None
) -> EngineerDecision:
    try:
        decision_row = EngineerDecision(
            task_id=ai_run.task_id,
            ai_run_id=ai_run.id,
            decision=decision,
            rationale=rationale,
            changes=changes,
            reviewer=None,
        )
        db.add(decision_row)
        db.commit()
        db.refresh(decision_row)
        return decision_row
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to record AI run decision.") from exc


def _parse_ai_run_public_id(ai_run_id: str) -> int | None:
    prefix = "AI-RUN-"
    if not ai_run_id.startswith(prefix):
        return None
    try:
        return int(ai_run_id[len(prefix) :])
    except ValueError:
        return None
