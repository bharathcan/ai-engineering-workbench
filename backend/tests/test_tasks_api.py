from app.api.deps import get_ai_provider_factory
from app.core.exceptions import AIProviderError
from app.main import app
from tests.support.analysis_payloads import (
    AMBIGUOUS_ANALYTICS_ANALYSIS,
    VALID_URL_SHORTENER_ANALYSIS,
)
from tests.support.fake_ai_provider import FakeAIProvider
from tests.support.task_plan_payloads import VALID_URL_SHORTENER_PLAN

URL_SHORTENER_TEXT = "Build a scalable URL shortener service with APIs, persistence, and analytics."


def _override_ai_provider(**kwargs):
    app.dependency_overrides[get_ai_provider_factory] = lambda: (
        lambda: FakeAIProvider(**kwargs)
    )


def _create_and_analyze(
    client, text=URL_SHORTENER_TEXT, analysis_payload=VALID_URL_SHORTENER_ANALYSIS
):
    _override_ai_provider(raw_payload=analysis_payload)
    create_response = client.post("/api/v1/requirements", json={"text": text})
    requirement_id = create_response.json()["id"]
    client.post(f"/api/v1/requirements/{requirement_id}/analyze")
    return requirement_id


def test_generate_plan_before_analysis_returns_409(client):
    create_response = client.post("/api/v1/requirements", json={"text": URL_SHORTENER_TEXT})
    requirement_id = create_response.json()["id"]

    response = client.post(f"/api/v1/requirements/{requirement_id}/tasks")
    assert response.status_code == 409


def test_generate_plan_for_unknown_requirement_returns_404(client):
    response = client.post("/api/v1/requirements/REQ-999999/tasks")
    assert response.status_code == 404


def test_full_flow_generate_plan_get_plan_get_task(client):
    requirement_id = _create_and_analyze(client)
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)

    generate_response = client.post(f"/api/v1/requirements/{requirement_id}/tasks")
    assert generate_response.status_code == 201
    plan = generate_response.json()
    assert plan["status"] == "GENERATED"
    assert plan["requirement_id"] == requirement_id
    assert len(plan["tasks"]) == 4
    assert plan["tasks"][0]["id"].startswith("TASK-")
    assert plan["tasks"][1]["dependencies"] == [plan["tasks"][0]["id"]]
    first_task_id = plan["tasks"][0]["id"]

    get_plan_response = client.get(f"/api/v1/requirements/{requirement_id}/tasks")
    assert get_plan_response.status_code == 200
    assert get_plan_response.json()["id"] == plan["id"]

    get_task_response = client.get(f"/api/v1/tasks/{first_task_id}")
    assert get_task_response.status_code == 200
    assert get_task_response.json()["title"] == plan["tasks"][0]["title"]
    assert get_task_response.json()["status"] == "REVIEW_REQUIRED"
    assert get_task_response.json()["review_status"] == "PENDING"


def test_plan_before_generation_returns_404(client):
    requirement_id = _create_and_analyze(client)
    response = client.get(f"/api/v1/requirements/{requirement_id}/tasks")
    assert response.status_code == 404


def test_get_unknown_task_returns_404(client):
    response = client.get("/api/v1/tasks/TASK-999999")
    assert response.status_code == 404


def test_material_ambiguity_blocks_plan_generation(client):
    requirement_id = _create_and_analyze(
        client, text="Improve the analytics.", analysis_payload=AMBIGUOUS_ANALYTICS_ANALYSIS
    )
    # If the decomposer were invoked, it would raise since no payload is set here.
    _override_ai_provider(error=AssertionError("AI should not be called when plan is blocked"))

    response = client.post(f"/api/v1/requirements/{requirement_id}/tasks")
    assert response.status_code == 201
    plan = response.json()
    assert plan["status"] == "BLOCKED"
    assert plan["tasks"] == []
    assert "AMB-001" in plan["blocked_reason"]
    assert "AMB-001" in plan["unresolved_ambiguities"]


def test_ai_provider_failure_returns_503(client):
    requirement_id = _create_and_analyze(client)
    _override_ai_provider(error=AIProviderError("simulated timeout"))

    response = client.post(f"/api/v1/requirements/{requirement_id}/tasks")
    assert response.status_code == 503


def test_malformed_plan_returns_502_and_does_not_persist(client):
    requirement_id = _create_and_analyze(client)
    _override_ai_provider(raw_payload={"summary": "incomplete", "tasks": []})

    response = client.post(f"/api/v1/requirements/{requirement_id}/tasks")
    assert response.status_code == 502

    get_response = client.get(f"/api/v1/requirements/{requirement_id}/tasks")
    assert get_response.status_code == 404


def test_decision_accept(client):
    requirement_id = _create_and_analyze(client)
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)
    plan = client.post(f"/api/v1/requirements/{requirement_id}/tasks").json()
    task_id = plan["tasks"][0]["id"]

    response = client.post(f"/api/v1/tasks/{task_id}/decision", json={"decision": "ACCEPT"})
    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "ACCEPT"
    assert body["status"] == "APPROVED"
    assert len(body["decisions"]) == 1
    assert body["decisions"][0]["decision"] == "ACCEPT"


def test_decision_modify_requires_rationale_and_changes(client):
    requirement_id = _create_and_analyze(client)
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)
    plan = client.post(f"/api/v1/requirements/{requirement_id}/tasks").json()
    task_id = plan["tasks"][0]["id"]

    missing_fields_response = client.post(
        f"/api/v1/tasks/{task_id}/decision", json={"decision": "MODIFY"}
    )
    assert missing_fields_response.status_code == 422

    response = client.post(
        f"/api/v1/tasks/{task_id}/decision",
        json={
            "decision": "MODIFY",
            "rationale": "Acceptance criteria too vague.",
            "changes": "Add a specific edge case for empty destination URLs.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "MODIFY"
    assert body["status"] == "NEEDS_REVISION"


def test_decision_reject_requires_rationale(client):
    requirement_id = _create_and_analyze(client)
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)
    plan = client.post(f"/api/v1/requirements/{requirement_id}/tasks").json()
    task_id = plan["tasks"][0]["id"]

    missing_rationale_response = client.post(
        f"/api/v1/tasks/{task_id}/decision", json={"decision": "REJECT"}
    )
    assert missing_rationale_response.status_code == 422

    response = client.post(
        f"/api/v1/tasks/{task_id}/decision",
        json={"decision": "REJECT", "rationale": "Out of scope for this milestone."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "REJECT"
    assert body["status"] == "REJECTED"


def test_decision_on_unknown_task_returns_404(client):
    response = client.post("/api/v1/tasks/TASK-999999/decision", json={"decision": "ACCEPT"})
    assert response.status_code == 404
