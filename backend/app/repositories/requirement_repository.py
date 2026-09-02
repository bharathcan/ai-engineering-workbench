from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError
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


def _parse_public_id(requirement_id: str) -> int | None:
    prefix = "REQ-"
    if not requirement_id.startswith(prefix):
        return None
    try:
        return int(requirement_id[len(prefix) :])
    except ValueError:
        return None
