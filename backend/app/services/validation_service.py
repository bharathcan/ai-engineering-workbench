from sqlalchemy.orm import Session

from app.core.exceptions import ArtifactNotFoundError, ValidationNotFoundError
from app.models.engineering_plan import Artifact, Validation
from app.repositories import artifact_repository, validation_repository
from app.schemas.validation import ValidationResponse
from app.services import validation_runner


def run_artifact_validation(
    db: Session, artifact_id: str, validation_type: str
) -> ValidationResponse:
    artifact = _get_artifact_or_raise(db, artifact_id)
    result = validation_runner.run_validation(validation_type)

    validation = validation_repository.save_validation(
        db,
        artifact,
        validation_type=validation_type,
        command=result.command,
        status=result.status,
        output=result.output,
        error=result.error,
        duration_ms=result.duration_ms,
        metadata=result.metadata,
    )
    return _to_response(validation)


def get_artifact_validations(db: Session, artifact_id: str) -> list[ValidationResponse]:
    artifact = _get_artifact_or_raise(db, artifact_id)
    validations = validation_repository.get_validations_for_artifact(db, artifact)
    return [_to_response(v) for v in validations]


def get_validation(db: Session, validation_id: str) -> ValidationResponse:
    validation = validation_repository.get_validation_by_public_id(db, validation_id)
    if validation is None:
        raise ValidationNotFoundError(validation_id)
    return _to_response(validation)


def _get_artifact_or_raise(db: Session, artifact_id: str) -> Artifact:
    artifact = artifact_repository.get_artifact_by_public_id(db, artifact_id)
    if artifact is None:
        raise ArtifactNotFoundError(artifact_id)
    return artifact


def _to_response(validation: Validation) -> ValidationResponse:
    return ValidationResponse(
        id=validation.public_id,
        artifact_id=validation.artifact.public_id,
        task_id=validation.task.public_id,
        validation_type=validation.validation_type,
        command=validation.command,
        status=validation.status,
        output=validation.output,
        evidence=_extract_evidence(validation),
        error=validation.error,
        duration_ms=validation.duration_ms,
        metadata=validation.metadata_,
        created_at=validation.created_at,
    )


def _extract_evidence(validation: Validation) -> str:
    """A short, human-scannable evidence line — e.g. 'evidence: 24 passed
    in 0.45s' from a pytest run — distinct from the full raw output."""
    if validation.status == "NOT_VALIDATED":
        return validation.error or "Not executed."
    lines = [line for line in validation.output.strip().splitlines() if line.strip()]
    if lines:
        return lines[-1].strip()
    if validation.error:
        return validation.error
    return "No output captured."
