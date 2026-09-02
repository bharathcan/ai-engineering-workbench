import difflib
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.ai.base import AIProvider
from app.ai.prompts import build_artifact_generation_user_prompt
from app.core.exceptions import (
    AIRunNotAcceptedError,
    AIRunNotFoundError,
    ArtifactNotFoundError,
    TaskNotFoundError,
)
from app.models.engineering_plan import AIRun, Artifact, EngineeringTask
from app.repositories import ai_run_repository, artifact_repository, engineering_plan_repository
from app.schemas.ai_recommendation import AIRecommendation
from app.schemas.artifact import ArtifactResponse
from app.services.artifact_generator import ArtifactGenerator
from app.services.decision_mapper import to_decision_response
from app.utils.safe_path import resolve_artifact_path


def generate_artifacts(
    db: Session, ai_run_id: str, ai_provider_factory: Callable[[], AIProvider]
) -> list[ArtifactResponse]:
    ai_run = _get_ai_run_or_raise(db, ai_run_id)

    latest_decision = ai_run.decisions[-1] if ai_run.decisions else None
    if latest_decision is None or latest_decision.decision != "ACCEPT":
        raise AIRunNotAcceptedError(
            ai_run_id, latest_decision.decision if latest_decision else "PENDING"
        )
    # Defensive: an ACCEPTed run should always be COMPLETED with a response,
    # but this guards against that invariant ever being violated silently.
    if ai_run.status != "COMPLETED" or not ai_run.response:
        raise AIRunNotAcceptedError(ai_run_id, ai_run.status)

    recommendation = AIRecommendation.model_validate(ai_run.response)
    task = ai_run.task

    user_prompt = build_artifact_generation_user_prompt(
        task_id=task.public_id,
        task_title=task.title,
        task_description=task.description,
        recommendation_summary=recommendation.summary,
        recommendation_approach=recommendation.approach,
        files_to_change=recommendation.files_to_change,
        proposed_changes=recommendation.proposed_changes,
        tests_to_add=recommendation.tests_to_add,
    )

    ai_provider = ai_provider_factory()
    result = ArtifactGenerator(ai_provider).generate(user_prompt)

    # Validate every proposed path before persisting or writing anything —
    # one unsafe path rejects the whole batch rather than silently dropping
    # it, so a partial, confusing write never happens.
    resolved_paths = [resolve_artifact_path(draft.path) for draft in result.artifacts]

    artifacts = artifact_repository.save_artifacts(
        db, task, ai_run, result.artifacts, resolved_paths
    )
    return [_to_artifact_response(db, task, a) for a in artifacts]


def get_task_artifacts(db: Session, task_id: str) -> list[ArtifactResponse]:
    task = _get_task_or_raise(db, task_id)
    artifacts = artifact_repository.get_artifacts_for_task(db, task)
    return [_to_artifact_response(db, task, a) for a in artifacts]


def get_artifact(db: Session, artifact_id: str) -> ArtifactResponse:
    artifact = _get_artifact_or_raise(db, artifact_id)
    return _to_artifact_response(db, artifact.task, artifact)


def decide_artifact(
    db: Session, artifact_id: str, decision: str, rationale: str | None, changes: str | None
) -> ArtifactResponse:
    artifact = _get_artifact_or_raise(db, artifact_id)
    artifact_repository.save_artifact_decision(db, artifact, decision, rationale, changes)
    return _to_artifact_response(db, artifact.task, artifact)


def _get_ai_run_or_raise(db: Session, ai_run_id: str) -> AIRun:
    run = ai_run_repository.get_ai_run_by_public_id(db, ai_run_id)
    if run is None:
        raise AIRunNotFoundError(ai_run_id)
    return run


def _get_task_or_raise(db: Session, task_id: str) -> EngineeringTask:
    task = engineering_plan_repository.get_task_by_public_id(db, task_id)
    if task is None:
        raise TaskNotFoundError(task_id)
    return task


def _get_artifact_or_raise(db: Session, artifact_id: str) -> Artifact:
    artifact = artifact_repository.get_artifact_by_public_id(db, artifact_id)
    if artifact is None:
        raise ArtifactNotFoundError(artifact_id)
    return artifact


def _to_artifact_response(
    db: Session, task: EngineeringTask, artifact: Artifact
) -> ArtifactResponse:
    previous_content = ""
    if artifact.supersedes_artifact_id:
        previous = artifact_repository.get_artifact_by_public_id(
            db, f"ARTIFACT-{artifact.supersedes_artifact_id:03d}"
        )
        if previous:
            previous_content = previous.content

    diff = _compute_diff(previous_content, artifact.content, artifact.path)

    return ArtifactResponse(
        id=artifact.public_id,
        task_id=task.public_id,
        ai_run_id=artifact.ai_run.public_id,
        artifact_type=artifact.artifact_type,
        path=artifact.path,
        content=artifact.content,
        description=artifact.description,
        status=artifact.status,
        version=artifact.version,
        supersedes_artifact_id=(
            f"ARTIFACT-{artifact.supersedes_artifact_id:03d}"
            if artifact.supersedes_artifact_id
            else None
        ),
        diff=diff,
        decisions=[to_decision_response(d) for d in artifact.decisions],
        created_at=artifact.created_at,
    )


def _compute_diff(before: str, after: str, path: str) -> str | None:
    if before == after:
        return None
    diff_lines = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
    )
    return "".join(diff_lines) or None
