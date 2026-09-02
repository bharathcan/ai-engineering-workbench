from collections.abc import Callable

from sqlalchemy.orm import Session

from app.ai.base import AIProvider
from app.core.exceptions import RequirementNotFoundError
from app.models.requirement import Requirement
from app.repositories import requirement_repository
from app.schemas.requirement import RequirementResponse
from app.schemas.requirement_analysis import RequirementAnalysisResult
from app.services.requirement_analyzer import RequirementAnalyzer


def create_requirement(db: Session, text: str) -> RequirementResponse:
    requirement = requirement_repository.create_requirement(db, text)
    return _to_response(requirement)


def get_requirement(db: Session, requirement_id: str) -> RequirementResponse:
    requirement = _get_or_raise(db, requirement_id)
    return _to_response(requirement)


def list_requirements(db: Session) -> list[RequirementResponse]:
    return [_to_response(r) for r in requirement_repository.list_requirements(db)]


def analyze_requirement(
    db: Session, requirement_id: str, ai_provider_factory: Callable[[], AIProvider]
) -> RequirementResponse:
    requirement = _get_or_raise(db, requirement_id)

    # Built only after the requirement is confirmed to exist — see
    # app.api.deps.get_ai_provider_factory for why this must stay lazy.
    analyzer = RequirementAnalyzer(ai_provider_factory())
    result: RequirementAnalysisResult = analyzer.analyze(requirement.text)

    requirement_repository.save_analysis(db, requirement, result)
    db.refresh(requirement)
    return _to_response(requirement)


def _get_or_raise(db: Session, requirement_id: str) -> Requirement:
    requirement = requirement_repository.get_requirement_by_public_id(db, requirement_id)
    if requirement is None:
        raise RequirementNotFoundError(requirement_id)
    return requirement


def _to_response(requirement: Requirement) -> RequirementResponse:
    latest_analysis = None
    if requirement.analyses:
        latest_analysis = requirement_repository.to_analysis_result(requirement.analyses[-1])

    return RequirementResponse(
        id=requirement.public_id,
        text=requirement.text,
        status=requirement.status,
        created_at=requirement.created_at,
        latest_analysis=latest_analysis,
    )
