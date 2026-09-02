import copy

import pytest

from app.core.exceptions import InvalidAIResponseError
from app.schemas.requirement_analysis import RequirementAnalysisResult
from app.services.task_decomposer import TaskDecomposer
from tests.support.analysis_payloads import VALID_URL_SHORTENER_ANALYSIS
from tests.support.fake_ai_provider import FakeAIProvider
from tests.support.task_plan_payloads import VALID_URL_SHORTENER_PLAN

ANALYSIS = RequirementAnalysisResult.model_validate(VALID_URL_SHORTENER_ANALYSIS)
REQUIREMENT_TEXT = "Build a scalable URL shortener service with APIs, persistence, and analytics."


def test_valid_plan_is_returned_with_tasks_and_dependencies():
    provider = FakeAIProvider(raw_payload=VALID_URL_SHORTENER_PLAN)
    result = TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)

    assert len(result.tasks) == 4
    assert result.tasks[0].id == "TASK-001"
    assert result.tasks[1].dependencies == ["TASK-001"]
    assert result.tasks[3].dependencies == ["TASK-002", "TASK-003"]


def test_every_task_references_a_real_analysis_id():
    provider = FakeAIProvider(raw_payload=VALID_URL_SHORTENER_PLAN)
    result = TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)

    valid_ids = {i.id for i in ANALYSIS.functional_requirements} | {
        i.id for i in ANALYSIS.non_functional_requirements
    }
    for task in result.tasks:
        assert set(task.requirement_refs) <= valid_ids | {
            i.id for i in ANALYSIS.constraints
        } | {i.id for i in ANALYSIS.success_criteria} | {
            i.id for i in ANALYSIS.engineering_concerns
        }
        assert len(task.requirement_refs) > 0


def test_empty_task_list_is_rejected():
    payload = {**VALID_URL_SHORTENER_PLAN, "tasks": []}
    provider = FakeAIProvider(raw_payload=payload)

    with pytest.raises(InvalidAIResponseError, match="empty task list"):
        TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)


def test_self_dependency_is_rejected():
    payload = copy.deepcopy(VALID_URL_SHORTENER_PLAN)
    payload["tasks"][0]["dependencies"] = ["TASK-001"]
    provider = FakeAIProvider(raw_payload=payload)

    with pytest.raises(InvalidAIResponseError, match="depends on itself"):
        TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)


def test_missing_referenced_task_is_rejected():
    payload = copy.deepcopy(VALID_URL_SHORTENER_PLAN)
    payload["tasks"][1]["dependencies"] = ["TASK-099"]
    provider = FakeAIProvider(raw_payload=payload)

    with pytest.raises(InvalidAIResponseError, match="unknown task id"):
        TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)


def test_circular_dependency_is_rejected():
    payload = copy.deepcopy(VALID_URL_SHORTENER_PLAN)
    # TASK-001 <-> TASK-002 depend on each other.
    payload["tasks"][0]["dependencies"] = ["TASK-002"]
    payload["tasks"][0]["sequence"] = 2
    payload["tasks"][1]["dependencies"] = ["TASK-001"]
    payload["tasks"][1]["sequence"] = 1
    provider = FakeAIProvider(raw_payload=payload)

    with pytest.raises(InvalidAIResponseError, match="Circular dependency"):
        TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)


def test_unknown_requirement_ref_is_rejected():
    payload = copy.deepcopy(VALID_URL_SHORTENER_PLAN)
    payload["tasks"][0]["requirement_refs"] = ["FR-999"]
    provider = FakeAIProvider(raw_payload=payload)

    with pytest.raises(InvalidAIResponseError, match="not present in the requirement analysis"):
        TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)


def test_sequence_inconsistent_with_dependency_is_rejected():
    payload = copy.deepcopy(VALID_URL_SHORTENER_PLAN)
    # TASK-002 depends on TASK-001 but is given an earlier sequence number.
    payload["tasks"][1]["sequence"] = 0
    provider = FakeAIProvider(raw_payload=payload)

    with pytest.raises(InvalidAIResponseError, match="does not come after its dependency"):
        TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)


def test_unsupported_task_type_is_rejected():
    payload = copy.deepcopy(VALID_URL_SHORTENER_PLAN)
    payload["tasks"][0]["type"] = "NOT_A_REAL_TYPE"
    provider = FakeAIProvider(raw_payload=payload)

    with pytest.raises(InvalidAIResponseError):
        TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)


def test_missing_task_field_is_rejected():
    payload = copy.deepcopy(VALID_URL_SHORTENER_PLAN)
    del payload["tasks"][0]["acceptance_criteria"]
    provider = FakeAIProvider(raw_payload=payload)

    with pytest.raises(InvalidAIResponseError):
        TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)


def test_duplicate_task_id_is_rejected():
    payload = copy.deepcopy(VALID_URL_SHORTENER_PLAN)
    payload["tasks"][1]["id"] = "TASK-001"
    provider = FakeAIProvider(raw_payload=payload)

    with pytest.raises(InvalidAIResponseError, match="Duplicate task id"):
        TaskDecomposer(provider).decompose(REQUIREMENT_TEXT, ANALYSIS)
