from collections.abc import Callable

from sqlalchemy.orm import Session

from app.ai.base import AIProvider
from app.ai.prompts import build_requirement_clarification_user_prompt
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


def clarify_requirement(
    db: Session,
    requirement_id: str,
    clarifications: str,
    ai_provider_factory: Callable[[], AIProvider],
) -> RequirementResponse:
    """Amends the same requirement in place with engineer-supplied
    clarifications, then re-analyzes. Safe to do in place (unlike a fresh
    requirement) because this only ever runs before any plan/task chain has
    been built on this requirement's analysis — see the ambiguity gate."""
    requirement = _get_or_raise(db, requirement_id)
    requirement = requirement_repository.append_clarification(db, requirement, clarifications)

    analyzer = RequirementAnalyzer(ai_provider_factory())

    # Get prior analysis to help AI preserve ID continuity during re-analysis
    prior_analysis = None
    if requirement.analyses:
        prior_analysis = requirement_repository.to_analysis_result(requirement.analyses[-1])
        prior_summary = f"Summary: {prior_analysis.summary}\nAmbiguities resolved: {[a.id for a in prior_analysis.ambiguities]}"
    else:
        prior_summary = ""

    # Use clarification-specific prompt to help AI preserve structure
    result: RequirementAnalysisResult = analyzer.analyze_with_context(
        requirement.text, clarifications, prior_summary
    )

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
