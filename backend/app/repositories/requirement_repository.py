from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError
from app.models.engineering_plan import (
    AIRun,
    Artifact,
    EngineerDecision,
    EngineeringPlan,
    EngineeringTask,
    Validation,
)
from app.models.requirement import Requirement, RequirementAnalysis
from app.schemas.requirement_analysis import RequirementAnalysisResult


def create_requirement(db: Session, text: str) -> Requirement:
    try:
        requirement = Requirement(text=text, status="CREATED")
        db.add(requirement)
        db.commit()
        db.refresh(requirement)
        return requirement
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to create requirement.") from exc


def list_requirements(db: Session) -> list[Requirement]:
    """Newest first — used by the Phase 11 project selector. No pagination
    yet; fine at this scale, revisit if requirement volume ever grows large
    enough for it to matter."""
    try:
        return db.query(Requirement).order_by(Requirement.id.desc()).all()
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to list requirements.") from exc


def append_clarification(db: Session, requirement: Requirement, clarifications: str) -> Requirement:
    try:
        requirement.text = (
            f"{requirement.text}\n\nEngineer clarifications:\n{clarifications}"
        )
        db.add(requirement)
        db.commit()
        db.refresh(requirement)
        return requirement
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to save clarification.") from exc


def get_requirement_by_public_id(db: Session, requirement_id: str) -> Requirement | None:
    numeric_id = _parse_public_id(requirement_id)
    if numeric_id is None:
        return None
    try:
        return db.get(Requirement, numeric_id)
    except SQLAlchemyError as exc:
        raise PersistenceError("Failed to load requirement.") from exc


def save_analysis(
    db: Session, requirement: Requirement, result: RequirementAnalysisResult
) -> RequirementAnalysis:
    try:
        analysis = RequirementAnalysis(
            requirement_id=requirement.id,
            summary=result.summary,
            functional_requirements=[item.model_dump() for item in result.functional_requirements],
            non_functional_requirements=[
                item.model_dump() for item in result.non_functional_requirements
            ],
            ambiguities=[item.model_dump() for item in result.ambiguities],
            assumptions=[item.model_dump() for item in result.assumptions],
            constraints=[item.model_dump() for item in result.constraints],
            success_criteria=[item.model_dump() for item in result.success_criteria],
            engineering_concerns=[item.model_dump() for item in result.engineering_concerns],
        )
        db.add(analysis)
        requirement.status = "ANALYZED"
        db.add(requirement)
        db.commit()
        db.refresh(analysis)
        return analysis
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to save requirement analysis.") from exc


def to_analysis_result(analysis: RequirementAnalysis) -> RequirementAnalysisResult:
    """Reconstructs the domain schema from a persisted row. Shared by
    requirement_service (for the API response) and engineering_plan_service
    (which feeds it to the TaskDecomposer) so there is one conversion, not
    two copies that could drift."""
    return RequirementAnalysisResult(
        summary=analysis.summary,
        functional_requirements=analysis.functional_requirements,
        non_functional_requirements=analysis.non_functional_requirements,
        ambiguities=analysis.ambiguities,
        assumptions=analysis.assumptions,
        constraints=analysis.constraints,
        success_criteria=analysis.success_criteria,
        engineering_concerns=analysis.engineering_concerns,
    )


def delete_requirement(db: Session, requirement: Requirement) -> None:
    """Deletes a requirement and everything traceable back to it: its
    analyses, plans, tasks, AI runs, artifacts, validations, and engineer
    decisions. No ON DELETE CASCADE exists at the DB level (see
    app.main — schema comes from create_all(), not migrations with explicit
    cascade rules), so this walks the tree leaf-to-root itself, in
    dependency order, within one transaction."""
    try:
        plan_ids = [
            row[0]
            for row in db.query(EngineeringPlan.id)
            .filter(EngineeringPlan.requirement_id == requirement.id)
            .all()
        ]

        if plan_ids:
            task_ids = [
                row[0]
                for row in db.query(EngineeringTask.id)
                .filter(EngineeringTask.plan_id.in_(plan_ids))
                .all()
            ]

            if task_ids:
                artifact_ids = [
                    row[0]
                    for row in db.query(Artifact.id)
                    .filter(Artifact.task_id.in_(task_ids))
                    .all()
                ]
                ai_run_ids = [
                    row[0]
                    for row in db.query(AIRun.id).filter(AIRun.task_id.in_(task_ids)).all()
                ]

                if artifact_ids:
                    db.query(Validation).filter(
                        Validation.artifact_id.in_(artifact_ids)
                    ).delete(synchronize_session=False)

                # Decisions reference task_id (always) plus optional
                # ai_run_id/artifact_id — filtering by task_id alone covers
                # every decision belonging to this requirement.
                db.query(EngineerDecision).filter(
                    EngineerDecision.task_id.in_(task_ids)
                ).delete(synchronize_session=False)

                if artifact_ids:
                    # Null out the self-referential FK first so deleting the
                    # batch doesn't trip over a row that supersedes another
                    # row in the same batch.
                    db.query(Artifact).filter(Artifact.id.in_(artifact_ids)).update(
                        {Artifact.supersedes_artifact_id: None}, synchronize_session=False
                    )
                    db.query(Artifact).filter(Artifact.id.in_(artifact_ids)).delete(
                        synchronize_session=False
                    )

                if ai_run_ids:
                    db.query(AIRun).filter(AIRun.id.in_(ai_run_ids)).update(
                        {AIRun.revised_from_ai_run_id: None}, synchronize_session=False
                    )
                    db.query(AIRun).filter(AIRun.id.in_(ai_run_ids)).delete(
                        synchronize_session=False
                    )

                db.query(EngineeringTask).filter(EngineeringTask.id.in_(task_ids)).delete(
                    synchronize_session=False
                )

            db.query(EngineeringPlan).filter(EngineeringPlan.id.in_(plan_ids)).delete(
                synchronize_session=False
            )

        db.query(RequirementAnalysis).filter(
            RequirementAnalysis.requirement_id == requirement.id
        ).delete(synchronize_session=False)

        db.delete(requirement)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to delete requirement.") from exc


def _parse_public_id(requirement_id: str) -> int | None:
    prefix = "REQ-"
    if not requirement_id.startswith(prefix):
        return None
    try:
        return int(requirement_id[len(prefix) :])
    except ValueError:
        return None
