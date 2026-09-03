import logging
from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.base import AIProvider
from app.api.deps import get_ai_provider_factory
from app.core.database import get_db
from app.core.exceptions import (
    AIProviderError,
    InvalidAIResponseError,
    PersistenceError,
    RequirementNotFoundError,
)
from app.schemas.requirement import (
    RequirementClarifyRequest,
    RequirementCreateRequest,
    RequirementResponse,
)
from app.services import requirement_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/requirements", tags=["requirements"])


@router.post("", response_model=RequirementResponse, status_code=201)
def create_requirement(payload: RequirementCreateRequest, db: Session = Depends(get_db)):
    try:
        return requirement_service.create_requirement(db, payload.text)
    except PersistenceError as exc:
        logger.error("Failed to create requirement: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to store the requirement.") from exc


@router.post("/{requirement_id}/analyze", response_model=RequirementResponse)
def analyze_requirement(
    requirement_id: str,
    db: Session = Depends(get_db),
    ai_provider_factory: Callable[[], AIProvider] = Depends(get_ai_provider_factory),
):
    try:
        return requirement_service.analyze_requirement(db, requirement_id, ai_provider_factory)
    except RequirementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIProviderError as exc:
        logger.error("AI provider failure analyzing %s: %s", requirement_id, exc)
        raise HTTPException(
            status_code=503, detail="The AI provider is currently unavailable. Try again later."
        ) from exc
    except InvalidAIResponseError as exc:
        logger.error("Invalid AI output analyzing %s: %s", requirement_id, exc)
        raise HTTPException(
            status_code=502,
            detail="The AI provider returned output that could not be validated.",
        ) from exc
    except PersistenceError as exc:
        logger.error("Failed to persist analysis for %s: %s", requirement_id, exc)
        raise HTTPException(status_code=500, detail="Failed to store the analysis.") from exc


@router.post("/{requirement_id}/clarify", response_model=RequirementResponse)
def clarify_requirement(
    requirement_id: str,
    payload: RequirementClarifyRequest,
    db: Session = Depends(get_db),
    ai_provider_factory: Callable[[], AIProvider] = Depends(get_ai_provider_factory),
):
    try:
        return requirement_service.clarify_requirement(
            db, requirement_id, payload.clarifications, ai_provider_factory
        )
    except RequirementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIProviderError as exc:
        logger.error("AI provider failure clarifying %s: %s", requirement_id, exc)
        raise HTTPException(
            status_code=503, detail="The AI provider is currently unavailable. Try again later."
        ) from exc
    except InvalidAIResponseError as exc:
        logger.error("Invalid AI output clarifying %s: %s", requirement_id, exc)
        raise HTTPException(
            status_code=502,
            detail="The AI provider returned output that could not be validated.",
        ) from exc
    except PersistenceError as exc:
        logger.error("Failed to persist clarification for %s: %s", requirement_id, exc)
        raise HTTPException(status_code=500, detail="Failed to store the clarification.") from exc


@router.get("", response_model=list[RequirementResponse])
def list_requirements(db: Session = Depends(get_db)):
    try:
        return requirement_service.list_requirements(db)
    except PersistenceError as exc:
        logger.error("Failed to list requirements: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to list requirements.") from exc


@router.get("/{requirement_id}", response_model=RequirementResponse)
def get_requirement(requirement_id: str, db: Session = Depends(get_db)):
    try:
        return requirement_service.get_requirement(db, requirement_id)
    except RequirementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to load requirement %s: %s", requirement_id, exc)
        raise HTTPException(status_code=500, detail="Failed to load the requirement.") from exc


@router.delete("/{requirement_id}", status_code=204)
def delete_requirement(requirement_id: str, db: Session = Depends(get_db)):
    try:
        requirement_service.delete_requirement(db, requirement_id)
    except RequirementNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to delete requirement %s: %s", requirement_id, exc)
        raise HTTPException(status_code=500, detail="Failed to delete the requirement.") from exc
