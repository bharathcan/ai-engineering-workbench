import logging
from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.base import AIProvider
from app.api.deps import get_ai_provider_factory
from app.core.database import get_db
from app.core.exceptions import (
    AIProviderError,
    EngineeringPlanNotFoundError,
    InvalidAIResponseError,
    PersistenceError,
    RequirementNotAnalyzedError,
    RequirementNotFoundError,
    TaskNotApprovedError,
    TaskNotFoundError,
)
from app.schemas.ai_run import AIAssistRequest, AIRunResponse
from app.schemas.engineering_plan import EngineeringPlanResponse, TaskDecisionRequest, TaskResponse
from app.services import ai_run_service, engineering_plan_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tasks"])


@router.post(
    "/api/v1/requirements/{requirement_id}/tasks",
    response_model=EngineeringPlanResponse,
    status_code=201,
)
def generate_plan(
    requirement_id: str,
    db: Session = Depends(get_db),
    ai_provider_factory: Callable[[], AIProvider] = Depends(get_ai_provider_factory),
):
    try:
        return engineering_plan_service.generate_plan(db, requirement_id, ai_provider_factory)
    except RequirementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RequirementNotAnalyzedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AIProviderError as exc:
        logger.error("AI provider failure decomposing %s: %s", requirement_id, exc)
        raise HTTPException(
            status_code=503, detail="The AI provider is currently unavailable. Try again later."
        ) from exc
    except InvalidAIResponseError as exc:
        logger.error("Invalid AI output decomposing %s: %s", requirement_id, exc)
        raise HTTPException(
            status_code=502,
            detail="The AI provider returned a task plan that could not be validated.",
        ) from exc
    except PersistenceError as exc:
        logger.error("Failed to persist plan for %s: %s", requirement_id, exc)
        raise HTTPException(
            status_code=500, detail="Failed to store the engineering plan."
        ) from exc


@router.get("/api/v1/requirements/{requirement_id}/tasks", response_model=EngineeringPlanResponse)
def get_plan(requirement_id: str, db: Session = Depends(get_db)):
    try:
        return engineering_plan_service.get_latest_plan(db, requirement_id)
    except RequirementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EngineeringPlanNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to load plan for %s: %s", requirement_id, exc)
        raise HTTPException(status_code=500, detail="Failed to load the engineering plan.") from exc


@router.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    try:
        return engineering_plan_service.get_task(db, task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to load task %s: %s", task_id, exc)
        raise HTTPException(status_code=500, detail="Failed to load the task.") from exc


@router.post("/api/v1/tasks/{task_id}/decision", response_model=TaskResponse)
def decide_task(task_id: str, payload: TaskDecisionRequest, db: Session = Depends(get_db)):
    try:
        return engineering_plan_service.decide_task(
            db, task_id, payload.decision, payload.rationale, payload.changes
        )
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to record decision for %s: %s", task_id, exc)
        raise HTTPException(status_code=500, detail="Failed to record the decision.") from exc


@router.post("/api/v1/tasks/{task_id}/ai-assist", response_model=AIRunResponse, status_code=201)
def request_ai_assistance(
    task_id: str,
    payload: AIAssistRequest,
    db: Session = Depends(get_db),
    ai_provider_factory: Callable[[], AIProvider] = Depends(get_ai_provider_factory),
):
    try:
        return ai_run_service.request_ai_assistance(
            db, task_id, payload.assistance_type, payload.instructions, ai_provider_factory
        )
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TaskNotApprovedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AIProviderError as exc:
        logger.error("AI provider failure assisting %s: %s", task_id, exc)
        raise HTTPException(
            status_code=503, detail="The AI provider is currently unavailable. Try again later."
        ) from exc
    except InvalidAIResponseError as exc:
        logger.error("Invalid AI output assisting %s: %s", task_id, exc)
        raise HTTPException(
            status_code=502,
            detail="The AI provider returned a recommendation that could not be validated.",
        ) from exc
    except PersistenceError as exc:
        logger.error("Failed to persist AI run for %s: %s", task_id, exc)
        raise HTTPException(status_code=500, detail="Failed to store the AI run.") from exc
