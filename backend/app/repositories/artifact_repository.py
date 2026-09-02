from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError
from app.models.engineering_plan import AIRun, Artifact, EngineerDecision, EngineeringTask
from app.schemas.artifact_generation import ArtifactDraftItem

DECISION_TO_STATUS = {"ACCEPT": "APPROVED", "MODIFY": "NEEDS_REVISION", "REJECT": "REJECTED"}


def get_latest_artifact_for_path(db: Session, task: EngineeringTask, path: str) -> Artifact | None:
    try:
        return (
            db.query(Artifact)
            .filter(Artifact.task_id == task.id, Artifact.path == path)
            .order_by(Artifact.version.desc())
            .first()
        )
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load prior artifact version.") from exc


def save_artifacts(
    db: Session,
    task: EngineeringTask,
    ai_run: AIRun,
    drafts: list[ArtifactDraftItem],
    resolved_paths: list[Path],
) -> list[Artifact]:
    """Persists each draft as a new Artifact row (versioned — never
    overwriting a prior row for the same task/path) and writes its content
    to the already-validated, already-resolved on-disk path. All paths must
    already be validated (app.utils.safe_path.resolve_artifact_path) before
    this is called — this function does not re-check them."""
    try:
        saved: list[Artifact] = []
        for draft, resolved_path in zip(drafts, resolved_paths, strict=True):
            previous = get_latest_artifact_for_path(db, task, draft.path)
            version = (previous.version + 1) if previous else 1

            artifact = Artifact(
                task_id=task.id,
                ai_run_id=ai_run.id,
                artifact_type=draft.artifact_type,
                path=draft.path,
                content=draft.content,
                description=draft.description,
                metadata_={},
                status="PENDING_REVIEW",
                version=version,
                supersedes_artifact_id=previous.id if previous else None,
            )
            db.add(artifact)
            db.flush()
            saved.append(artifact)

            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            resolved_path.write_text(draft.content)

        db.commit()
        for artifact in saved:
            db.refresh(artifact)
        return saved
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to save generated artifacts.") from exc


def get_artifact_by_public_id(db: Session, artifact_id: str) -> Artifact | None:
    numeric_id = _parse_artifact_public_id(artifact_id)
    if numeric_id is None:
        return None
    try:
        return db.get(Artifact, numeric_id)
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load artifact.") from exc


def get_artifacts_for_task(db: Session, task: EngineeringTask) -> list[Artifact]:
    try:
        return (
            db.query(Artifact)
            .filter(Artifact.task_id == task.id)
            .order_by(Artifact.id)
            .all()
        )
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load artifacts for task.") from exc


def save_artifact_decision(
    db: Session, artifact: Artifact, decision: str, rationale: str | None, changes: str | None
) -> EngineerDecision:
    try:
        decision_row = EngineerDecision(
            task_id=artifact.task_id,
            artifact_id=artifact.id,
            decision=decision,
            rationale=rationale,
            changes=changes,
            reviewer=None,
        )
        db.add(decision_row)
        artifact.status = DECISION_TO_STATUS[decision]
        db.add(artifact)
        db.commit()
        db.refresh(decision_row)
        db.refresh(artifact)
        return decision_row
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to record artifact decision.") from exc


def _parse_artifact_public_id(artifact_id: str) -> int | None:
    prefix = "ARTIFACT-"
    if not artifact_id.startswith(prefix):
        return None
    try:
        return int(artifact_id[len(prefix) :])
    except ValueError:
        return None
