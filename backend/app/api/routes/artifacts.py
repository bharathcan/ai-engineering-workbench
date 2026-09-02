import logging
from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.base import AIProvider
from app.api.deps import get_ai_provider_factory
from app.core.database import get_db
from app.core.exceptions import (
    AIProviderError,
    AIRunNotAcceptedError,
    AIRunNotFoundError,
    ArtifactNotFoundError,
    InvalidAIResponseError,
    PersistenceError,
    TaskNotFoundError,
    UnsafeArtifactPathError,
)
from app.schemas.artifact import ArtifactDecisionRequest, ArtifactResponse
from app.services import artifact_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["artifacts"])


@router.post(
    "/api/v1/ai-runs/{ai_run_id}/artifacts",
    response_model=list[ArtifactResponse],
    status_code=201,
)
def generate_artifacts(
    ai_run_id: str,
    db: Session = Depends(get_db),
    ai_provider_factory: Callable[[], AIProvider] = Depends(get_ai_provider_factory),
):
    try:
        return artifact_service.generate_artifacts(db, ai_run_id, ai_provider_factory)
    except AIRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AIRunNotAcceptedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UnsafeArtifactPathError as exc:
        logger.warning("Rejected unsafe artifact path for AI run %s: %s", ai_run_id, exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AIProviderError as exc:
        logger.error("AI provider failure generating artifacts for %s: %s", ai_run_id, exc)
        raise HTTPException(
            status_code=503, detail="The AI provider is currently unavailable. Try again later."
        ) from exc
    except InvalidAIResponseError as exc:
        logger.error("Invalid AI output generating artifacts for %s: %s", ai_run_id, exc)
        raise HTTPException(
            status_code=502,
            detail="The AI provider returned artifacts that could not be validated.",
        ) from exc
    except PersistenceError as exc:
        logger.error("Failed to persist artifacts for %s: %s", ai_run_id, exc)
        raise HTTPException(
            status_code=500, detail="Failed to store the generated artifacts."
        ) from exc


@router.get("/api/v1/tasks/{task_id}/artifacts", response_model=list[ArtifactResponse])
def get_task_artifacts(task_id: str, db: Session = Depends(get_db)):
    try:
        return artifact_service.get_task_artifacts(db, task_id)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to load artifacts for %s: %s", task_id, exc)
        raise HTTPException(status_code=500, detail="Failed to load artifacts.") from exc


@router.get("/api/v1/artifacts/{artifact_id}", response_model=ArtifactResponse)
def get_artifact(artifact_id: str, db: Session = Depends(get_db)):
    try:
        return artifact_service.get_artifact(db, artifact_id)
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to load artifact %s: %s", artifact_id, exc)
        raise HTTPException(status_code=500, detail="Failed to load the artifact.") from exc


@router.post("/api/v1/artifacts/{artifact_id}/decision", response_model=ArtifactResponse)
def decide_artifact(
    artifact_id: str, payload: ArtifactDecisionRequest, db: Session = Depends(get_db)
):
    try:
        return artifact_service.decide_artifact(
            db, artifact_id, payload.decision, payload.rationale, payload.changes
        )
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to record decision for %s: %s", artifact_id, exc)
        raise HTTPException(status_code=500, detail="Failed to record the decision.") from exc
