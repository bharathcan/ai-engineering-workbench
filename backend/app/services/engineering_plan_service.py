from collections.abc import Callable

from sqlalchemy.orm import Session

from app.ai.base import AIProvider
from app.core.exceptions import (
    EngineeringPlanNotFoundError,
    RequirementNotAnalyzedError,
    RequirementNotFoundError,
    TaskNotFoundError,
)
from app.models.engineering_plan import EngineeringPlan, EngineeringTask
from app.models.requirement import Requirement
from app.repositories import engineering_plan_repository, requirement_repository
from app.schemas.engineering_plan import EngineeringPlanResponse, TaskResponse
from app.services.ai_run_mapper import to_ai_run_response
from app.services.decision_mapper import to_decision_response
from app.services.task_decomposer import TaskDecomposer

# An ambiguity blocks planning if its impact is HIGH. This threshold is not
# specified by any requirement — it is this codebase's own resolution of
# what "material ambiguity" means, and is deliberately documented as such
# rather than left implicit. See docs/api-design.md.
BLOCKING_AMBIGUITY_IMPACT = "HIGH"


def generate_plan(
    db: Session, requirement_id: str, ai_provider_factory: Callable[[], AIProvider]
) -> EngineeringPlanResponse:
    requirement = _get_requirement_or_raise(db, requirement_id)
    if requirement.status != "ANALYZED" or not requirement.analyses:
        raise RequirementNotAnalyzedError(requirement_id)

    analysis_row = requirement.analyses[-1]
    analysis = requirement_repository.to_analysis_result(analysis_row)

    material_ambiguities = [
        a for a in analysis.ambiguities if a.impact == BLOCKING_AMBIGUITY_IMPACT
    ]
    if material_ambiguities:
        reason = (
            "Material requirement ambiguities remain unresolved. Required engineer "
            "action: clarify " + ", ".join(a.id for a in material_ambiguities) + " before "
            "task generation. (An ambiguity is treated as material, and blocks planning, "
            f"when its impact is {BLOCKING_AMBIGUITY_IMPACT}.)"
        )
        plan = engineering_plan_repository.save_blocked_plan(
            db,
            requirement,
            analysis_row,
            reason,
            unresolved_ambiguity_ids=[a.id for a in material_ambiguities],
        )
        return _to_plan_response(plan)

    non_blocking_ambiguity_ids = [a.id for a in analysis.ambiguities]

    decomposer = TaskDecomposer(ai_provider_factory())
    decomposition = decomposer.decompose(requirement.text, analysis)

    plan = engineering_plan_repository.save_generated_plan(
        db, requirement, analysis_row, decomposition, non_blocking_ambiguity_ids
    )
    return _to_plan_response(plan)


def get_latest_plan(db: Session, requirement_id: str) -> EngineeringPlanResponse:
    requirement = _get_requirement_or_raise(db, requirement_id)
    plan = engineering_plan_repository.get_latest_plan_by_requirement(db, requirement)
    if plan is None:
        raise EngineeringPlanNotFoundError(requirement_id)
    return _to_plan_response(plan)


def get_task(db: Session, task_id: str) -> TaskResponse:
    task = _get_task_or_raise(db, task_id)
    return _to_task_response(task)


def decide_task(
    db: Session, task_id: str, decision: str, rationale: str | None, changes: str | None
) -> TaskResponse:
    task = _get_task_or_raise(db, task_id)
    engineering_plan_repository.save_decision(db, task, decision, rationale, changes)
    return _to_task_response(task)


def _get_requirement_or_raise(db: Session, requirement_id: str) -> Requirement:
    requirement = requirement_repository.get_requirement_by_public_id(db, requirement_id)
    if requirement is None:
        raise RequirementNotFoundError(requirement_id)
    return requirement


def _get_task_or_raise(db: Session, task_id: str) -> EngineeringTask:
    task = engineering_plan_repository.get_task_by_public_id(db, task_id)
    if task is None:
        raise TaskNotFoundError(task_id)
    return task


def _to_task_response(task: EngineeringTask) -> TaskResponse:
    return TaskResponse(
        id=task.public_id,
        plan_id=task.plan.public_id,
        title=task.title,
        description=task.description,
        type=task.type,
        requirement_refs=task.requirement_refs,
        dependencies=task.dependencies,
        sequence=task.sequence,
        acceptance_criteria=task.acceptance_criteria,
        ai_assistance_type=task.ai_assistance_type,
        risks=task.risks,
        status=task.status,
        review_status=task.review_status,
        decisions=[to_decision_response(d) for d in task.decisions],
        ai_runs=[to_ai_run_response(r) for r in task.ai_runs],
        created_at=task.created_at,
    )


def _to_plan_response(plan: EngineeringPlan) -> EngineeringPlanResponse:
    return EngineeringPlanResponse(
        id=plan.public_id,
        requirement_id=plan.requirement.public_id,
        requirement_analysis_id=f"ANALYSIS-{plan.requirement_analysis_id:03d}",
        status=plan.status,
        blocked_reason=plan.blocked_reason,
        summary=plan.summary,
        tasks=[_to_task_response(task) for task in plan.tasks],
        assumptions=plan.assumptions,
        unresolved_ambiguities=plan.unresolved_ambiguities,
        risks=plan.risks,
        review_status=plan.review_status,
        created_at=plan.created_at,
    )
