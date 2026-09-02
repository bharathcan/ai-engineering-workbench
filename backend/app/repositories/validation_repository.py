from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError
from app.models.engineering_plan import Artifact, Validation


def save_validation(
    db: Session,
    artifact: Artifact,
    *,
    validation_type: str,
    command: str,
    status: str,
    output: str,
    error: str | None,
    duration_ms: int,
    metadata: dict,
) -> Validation:
    try:
        validation = Validation(
            artifact_id=artifact.id,
            task_id=artifact.task_id,
            validation_type=validation_type,
            command=command,
            status=status,
            output=output,
            error=error,
            duration_ms=duration_ms,
            metadata_=metadata,
        )
        db.add(validation)
        db.commit()
        db.refresh(validation)
        return validation
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to save validation result.") from exc


def get_validation_by_public_id(db: Session, validation_id: str) -> Validation | None:
    numeric_id = _parse_validation_public_id(validation_id)
    if numeric_id is None:
        return None
    try:
        return db.get(Validation, numeric_id)
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load validation.") from exc


def get_validations_for_artifact(db: Session, artifact: Artifact) -> list[Validation]:
    try:
        return (
            db.query(Validation)
            .filter(Validation.artifact_id == artifact.id)
            .order_by(Validation.id)
            .all()
        )
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load validations for artifact.") from exc


def _parse_validation_public_id(validation_id: str) -> int | None:
    prefix = "VALIDATION-"
    if not validation_id.startswith(prefix):
        return None
    try:
        return int(validation_id[len(prefix) :])
    except ValueError:
        return None
