from app.api.deps import get_ai_provider_factory
from app.core.exceptions import AIProviderError
from app.main import app
from tests.support.ai_recommendation_payloads import VALID_RECOMMENDATION
from tests.support.analysis_payloads import VALID_URL_SHORTENER_ANALYSIS
from tests.support.fake_ai_provider import FakeAIProvider
from tests.support.task_plan_payloads import VALID_URL_SHORTENER_PLAN

URL_SHORTENER_TEXT = "Build a scalable URL shortener service with APIs, persistence, and analytics."


def _override_ai_provider(**kwargs):
    app.dependency_overrides[get_ai_provider_factory] = lambda: (
        lambda: FakeAIProvider(**kwargs)
    )


def _create_approved_task(client) -> str:
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_ANALYSIS)
    create_response = client.post("/api/v1/requirements", json={"text": URL_SHORTENER_TEXT})
    requirement_id = create_response.json()["id"]
    client.post(f"/api/v1/requirements/{requirement_id}/analyze")

    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)
    plan = client.post(f"/api/v1/requirements/{requirement_id}/tasks").json()
    task_id = plan["tasks"][0]["id"]

    client.post(f"/api/v1/tasks/{task_id}/decision", json={"decision": "ACCEPT"})
    return task_id


def test_ai_assist_on_unknown_task_returns_404(client):
    response = client.post(
        "/api/v1/tasks/TASK-999999/ai-assist",
        json={"assistance_type": "CODE_GENERATION"},
    )
    assert response.status_code == 404


def test_ai_assist_on_unapproved_task_returns_409(client):
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_ANALYSIS)
    create_response = client.post("/api/v1/requirements", json={"text": URL_SHORTENER_TEXT})
    requirement_id = create_response.json()["id"]
    client.post(f"/api/v1/requirements/{requirement_id}/analyze")
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)
    plan = client.post(f"/api/v1/requirements/{requirement_id}/tasks").json()
    task_id = plan["tasks"][0]["id"]  # never ACCEPTed — still REVIEW_REQUIRED

    response = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    )
    assert response.status_code == 409


def test_ai_assist_rejects_unsupported_assistance_type(client):
    task_id = _create_approved_task(client)
    response = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "NOT_A_REAL_TYPE"}
    )
    assert response.status_code == 422


def test_ai_assist_rejects_none_as_assistance_type(client):
    # AIAssistRequestType deliberately excludes "NONE" — see app/schemas/ai_run.py.
    task_id = _create_approved_task(client)
    response = client.post(f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "NONE"})
    assert response.status_code == 422


def test_successful_ai_assist_returns_recommendation(client):
    task_id = _create_approved_task(client)
    _override_ai_provider(raw_payload=VALID_RECOMMENDATION)

    response = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist",
        json={"assistance_type": "CODE_GENERATION", "instructions": "Implement it."},
    )
    assert response.status_code == 201
    run = response.json()
    assert run["id"].startswith("AI-RUN-")
    assert run["task_id"] == task_id
    assert run["status"] == "COMPLETED"
    assert run["response"]["confidence"] == "MEDIUM"
    assert run["response"]["summary"] == "Use a unique database constraint."
    assert run["error"] is None
    assert run["decisions"] == []
    assert run["revised_from_ai_run_id"] is None
    assert "prompt" not in run  # not exposed via the API — see docs/api-design.md


def test_ai_provider_failure_returns_503_and_persists_failed_run(client):
    task_id = _create_approved_task(client)
    _override_ai_provider(error=AIProviderError("simulated timeout with sensitive-looking data"))

    response = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    )
    assert response.status_code == 503

    task = client.get(f"/api/v1/tasks/{task_id}").json()
    assert len(task["ai_runs"]) == 1
    failed_run = task["ai_runs"][0]
    assert failed_run["status"] == "FAILED"
    assert failed_run["response"] is None
    # The persisted/returned error is a generic classification, never the
    # raw provider exception text (which could contain sensitive detail).
    assert failed_run["error"] == "The AI provider request failed."
    assert "sensitive-looking data" not in failed_run["error"]


def test_invalid_ai_response_returns_502_and_persists_failed_run(client):
    task_id = _create_approved_task(client)
    _override_ai_provider(raw_payload={"summary": "incomplete, missing required fields"})

    response = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    )
    assert response.status_code == 502

    task = client.get(f"/api/v1/tasks/{task_id}").json()
    assert len(task["ai_runs"]) == 1
    assert task["ai_runs"][0]["status"] == "FAILED"
    assert task["ai_runs"][0]["response"] is None


def test_decision_accept_on_ai_run(client):
    task_id = _create_approved_task(client)
    _override_ai_provider(raw_payload=VALID_RECOMMENDATION)
    run = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    ).json()

    response = client.post(
        f"/api/v1/ai-runs/{run['id']}/decision",
        json={"decision": "ACCEPT", "rationale": "Matches the task requirements."},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["decisions"]) == 1
    assert body["decisions"][0]["decision"] == "ACCEPT"
    assert body["decisions"][0]["ai_run_id"] == run["id"]
    assert body["decisions"][0]["reviewer"] is None  # no auth exists — documented limitation


def test_decision_reject_requires_rationale(client):
    task_id = _create_approved_task(client)
    _override_ai_provider(raw_payload=VALID_RECOMMENDATION)
    run = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    ).json()

    missing_rationale = client.post(
        f"/api/v1/ai-runs/{run['id']}/decision", json={"decision": "REJECT"}
    )
    assert missing_rationale.status_code == 422

    response = client.post(
        f"/api/v1/ai-runs/{run['id']}/decision",
        json={"decision": "REJECT", "rationale": "Does not satisfy scalability requirement."},
    )
    assert response.status_code == 200
    assert response.json()["decisions"][0]["decision"] == "REJECT"


def test_decision_on_unknown_ai_run_returns_404(client):
    response = client.post(
        "/api/v1/ai-runs/AI-RUN-999999/decision", json={"decision": "ACCEPT"}
    )
    assert response.status_code == 404


def test_modify_then_revision_preserves_first_run_and_links_second(client):
    task_id = _create_approved_task(client)

    # AI-RUN-001
    _override_ai_provider(raw_payload=VALID_RECOMMENDATION)
    run_1 = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    ).json()

    modify_response = client.post(
        f"/api/v1/ai-runs/{run_1['id']}/decision",
        json={
            "decision": "MODIFY",
            "rationale": "Need a database uniqueness constraint.",
            "changes": "Add unique constraint and retry handling.",
        },
    )
    assert modify_response.status_code == 200

    # AI-RUN-002 — a second request for the same task after MODIFY.
    revised_recommendation = {**VALID_RECOMMENDATION, "summary": "Revised: added retry handling."}
    _override_ai_provider(raw_payload=revised_recommendation)
    run_2_response = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    )
    assert run_2_response.status_code == 201
    run_2 = run_2_response.json()

    assert run_2["id"] != run_1["id"]
    assert run_2["revised_from_ai_run_id"] == run_1["id"]
    assert run_2["response"]["summary"] == "Revised: added retry handling."

    # AI-RUN-001 must still exist, unmodified, with its MODIFY decision intact.
    task = client.get(f"/api/v1/tasks/{task_id}").json()
    assert len(task["ai_runs"]) == 2
    run_ids = {r["id"] for r in task["ai_runs"]}
    assert run_ids == {run_1["id"], run_2["id"]}
    original = next(r for r in task["ai_runs"] if r["id"] == run_1["id"])
    assert original["response"]["summary"] == "Use a unique database constraint."
    assert original["decisions"][0]["decision"] == "MODIFY"

    # Accept the revision.
    accept_response = client.post(
        f"/api/v1/ai-runs/{run_2['id']}/decision", json={"decision": "ACCEPT"}
    )
    assert accept_response.status_code == 200


def test_traceability_task_to_ai_run_to_decision(client):
    task_id = _create_approved_task(client)
    _override_ai_provider(raw_payload=VALID_RECOMMENDATION)
    run = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    ).json()
    client.post(f"/api/v1/ai-runs/{run['id']}/decision", json={"decision": "ACCEPT"})

    task = client.get(f"/api/v1/tasks/{task_id}").json()
    assert task["id"] == task_id
    assert len(task["ai_runs"]) == 1
    assert task["ai_runs"][0]["id"] == run["id"]
    assert task["ai_runs"][0]["decisions"][0]["decision"] == "ACCEPT"
