from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError
from app.models.engineering_plan import EngineerDecision, EngineeringPlan, EngineeringTask
from app.models.requirement import Requirement, RequirementAnalysis
from app.schemas.task_decomposition import TaskDecompositionResult

DECISION_TO_STATUS = {"ACCEPT": "APPROVED", "MODIFY": "NEEDS_REVISION", "REJECT": "REJECTED"}


def save_blocked_plan(
    db: Session,
    requirement: Requirement,
    analysis: RequirementAnalysis,
    reason: str,
    unresolved_ambiguity_ids: list[str],
) -> EngineeringPlan:
    try:
        plan = EngineeringPlan(
            requirement_id=requirement.id,
            requirement_analysis_id=analysis.id,
            status="BLOCKED",
            blocked_reason=reason,
            summary="",
            assumptions=[],
            unresolved_ambiguities=unresolved_ambiguity_ids,
            risks=[],
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to record blocked plan.") from exc


def save_generated_plan(
    db: Session,
    requirement: Requirement,
    analysis: RequirementAnalysis,
    decomposition: TaskDecompositionResult,
    unresolved_ambiguity_ids: list[str],
) -> EngineeringPlan:
    try:
        plan = EngineeringPlan(
            requirement_id=requirement.id,
            requirement_analysis_id=analysis.id,
            status="GENERATED",
            blocked_reason=None,
            summary=decomposition.summary,
            assumptions=decomposition.assumptions,
            unresolved_ambiguities=unresolved_ambiguity_ids,
            risks=[item.model_dump() for item in decomposition.risks],
        )
        db.add(plan)
        db.flush()  # assign plan.id without ending the transaction

        # Two passes: tasks are inserted first to obtain their global public
        # ids, then dependencies (given by the AI as plan-local ids) are
        # remapped to those global ids — see app.schemas.task_decomposition.
        local_to_global: dict[str, str] = {}
        rows_with_source: list[tuple[EngineeringTask, object]] = []
        for item in decomposition.tasks:
            row = EngineeringTask(
                plan_id=plan.id,
                title=item.title,
                description=item.description,
                type=item.type,
                requirement_refs=item.requirement_refs,
                dependencies=[],
                sequence=item.sequence,
                acceptance_criteria=item.acceptance_criteria,
                ai_assistance_type=item.ai_assistance_type,
                risks=[risk.model_dump() for risk in item.risks],
            )
            db.add(row)
            db.flush()
            local_to_global[item.id] = row.public_id
            rows_with_source.append((row, item))

        for row, item in rows_with_source:
            row.dependencies = [local_to_global[dep_id] for dep_id in item.dependencies]

        db.commit()
        db.refresh(plan)
        return plan
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to save engineering plan.") from exc


def get_latest_plan_by_requirement(
    db: Session, requirement: Requirement
) -> EngineeringPlan | None:
    try:
        return (
            db.query(EngineeringPlan)
            .filter(EngineeringPlan.requirement_id == requirement.id)
            .order_by(EngineeringPlan.id.desc())
            .first()
        )
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load engineering plan.") from exc


def get_task_by_public_id(db: Session, task_id: str) -> EngineeringTask | None:
    numeric_id = _parse_task_public_id(task_id)
    if numeric_id is None:
        return None
    try:
        return db.get(EngineeringTask, numeric_id)
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load task.") from exc


def save_decision(
    db: Session, task: EngineeringTask, decision: str, rationale: str | None, changes: str | None
) -> EngineerDecision:
    try:
        decision_row = EngineerDecision(
            task_id=task.id, decision=decision, rationale=rationale, changes=changes
        )
        db.add(decision_row)
        task.review_status = decision
        task.status = DECISION_TO_STATUS[decision]
        db.add(task)
        db.commit()
        db.refresh(decision_row)
        db.refresh(task)
        return decision_row
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to record engineer decision.") from exc


def _parse_task_public_id(task_id: str) -> int | None:
    prefix = "TASK-"
    if not task_id.startswith(prefix):
        return None
    try:
        return int(task_id[len(prefix) :])
    except ValueError:
        return None
