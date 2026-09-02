import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import (
    ArtifactNotFoundError,
    PersistenceError,
    UnsupportedValidationTypeError,
    ValidationNotFoundError,
)
from app.schemas.validation import ValidationRequest, ValidationResponse
from app.services import validation_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["validations"])


@router.post(
    "/api/v1/artifacts/{artifact_id}/validate", response_model=ValidationResponse, status_code=201
)
def validate_artifact(artifact_id: str, payload: ValidationRequest, db: Session = Depends(get_db)):
    try:
        return validation_service.run_artifact_validation(db, artifact_id, payload.validation_type)
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnsupportedValidationTypeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to persist validation for %s: %s", artifact_id, exc)
        raise HTTPException(
            status_code=500, detail="Failed to store the validation result."
        ) from exc


@router.get("/api/v1/artifacts/{artifact_id}/validations", response_model=list[ValidationResponse])
def get_artifact_validations(artifact_id: str, db: Session = Depends(get_db)):
    try:
        return validation_service.get_artifact_validations(db, artifact_id)
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to load validations for %s: %s", artifact_id, exc)
        raise HTTPException(status_code=500, detail="Failed to load validations.") from exc


@router.get("/api/v1/validations/{validation_id}", response_model=ValidationResponse)
def get_validation(validation_id: str, db: Session = Depends(get_db)):
    try:
        return validation_service.get_validation(db, validation_id)
    except ValidationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PersistenceError as exc:
        logger.error("Failed to load validation %s: %s", validation_id, exc)
        raise HTTPException(status_code=500, detail="Failed to load the validation.") from exc
