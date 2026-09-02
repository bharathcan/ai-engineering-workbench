from pathlib import Path

from app.api.deps import get_ai_provider_factory
from app.core.exceptions import AIProviderError, PersistenceError
from app.main import app
from app.repositories import artifact_repository
from app.utils import safe_path
from tests.support.ai_recommendation_payloads import VALID_RECOMMENDATION
from tests.support.analysis_payloads import VALID_URL_SHORTENER_ANALYSIS
from tests.support.artifact_payloads import (
    MULTI_FILE_ARTIFACT_GENERATION,
    REVISED_ARTIFACT_GENERATION,
    UNSAFE_ABSOLUTE_PATH_ARTIFACT_GENERATION,
    UNSAFE_PATH_ARTIFACT_GENERATION,
    VALID_ARTIFACT_GENERATION,
)
from tests.support.fake_ai_provider import FakeAIProvider
from tests.support.task_plan_payloads import VALID_URL_SHORTENER_PLAN

URL_SHORTENER_TEXT = "Build a scalable URL shortener service with APIs, persistence, and analytics."


def _override_ai_provider(**kwargs):
    app.dependency_overrides[get_ai_provider_factory] = lambda: (
        lambda: FakeAIProvider(**kwargs)
    )


def _create_accepted_ai_run(client) -> str:
    """Walks create -> analyze -> plan -> accept task -> ai-assist -> accept
    run, returning the accepted ai_run_id."""
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_ANALYSIS)
    create_response = client.post("/api/v1/requirements", json={"text": URL_SHORTENER_TEXT})
    requirement_id = create_response.json()["id"]
    client.post(f"/api/v1/requirements/{requirement_id}/analyze")

    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)
    plan = client.post(f"/api/v1/requirements/{requirement_id}/tasks").json()
    task_id = plan["tasks"][0]["id"]
    client.post(f"/api/v1/tasks/{task_id}/decision", json={"decision": "ACCEPT"})

    _override_ai_provider(raw_payload=VALID_RECOMMENDATION)
    run = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    ).json()
    client.post(f"/api/v1/ai-runs/{run['id']}/decision", json={"decision": "ACCEPT"})
    return run["id"]


def test_generate_artifacts_for_unknown_ai_run_returns_404(client):
    response = client.post("/api/v1/ai-runs/AI-RUN-999999/artifacts")
    assert response.status_code == 404


def test_generate_artifacts_for_unaccepted_ai_run_returns_409(client):
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_ANALYSIS)
    create_response = client.post("/api/v1/requirements", json={"text": URL_SHORTENER_TEXT})
    requirement_id = create_response.json()["id"]
    client.post(f"/api/v1/requirements/{requirement_id}/analyze")
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)
    plan = client.post(f"/api/v1/requirements/{requirement_id}/tasks").json()
    task_id = plan["tasks"][0]["id"]
    client.post(f"/api/v1/tasks/{task_id}/decision", json={"decision": "ACCEPT"})

    _override_ai_provider(raw_payload=VALID_RECOMMENDATION)
    run = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    ).json()
    # Never decided — still PENDING.

    response = client.post(f"/api/v1/ai-runs/{run['id']}/artifacts")
    assert response.status_code == 409


def test_generate_artifacts_for_rejected_ai_run_returns_409(client):
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_ANALYSIS)
    create_response = client.post("/api/v1/requirements", json={"text": URL_SHORTENER_TEXT})
    requirement_id = create_response.json()["id"]
    client.post(f"/api/v1/requirements/{requirement_id}/analyze")
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)
    plan = client.post(f"/api/v1/requirements/{requirement_id}/tasks").json()
    task_id = plan["tasks"][0]["id"]
    client.post(f"/api/v1/tasks/{task_id}/decision", json={"decision": "ACCEPT"})

    _override_ai_provider(raw_payload=VALID_RECOMMENDATION)
    run = client.post(
        f"/api/v1/tasks/{task_id}/ai-assist", json={"assistance_type": "CODE_GENERATION"}
    ).json()
    client.post(
        f"/api/v1/ai-runs/{run['id']}/decision", json={"decision": "REJECT", "rationale": "No."}
    )

    response = client.post(f"/api/v1/ai-runs/{run['id']}/artifacts")
    assert response.status_code == 409


def test_successful_artifact_generation_writes_file_and_persists(client, tmp_path):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(raw_payload=VALID_ARTIFACT_GENERATION)

    response = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts")
    assert response.status_code == 201
    artifacts = response.json()
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact["id"].startswith("ARTIFACT-")
    assert artifact["ai_run_id"] == ai_run_id
    assert artifact["artifact_type"] == "SOURCE_CODE"
    assert artifact["path"] == "backend/app/services/url_service.py"
    assert artifact["status"] == "PENDING_REVIEW"
    assert artifact["version"] == 1
    assert artifact["supersedes_artifact_id"] is None
    assert artifact["diff"] is not None  # version 1 diffs against empty

    written_file = Path(safe_path.ARTIFACT_WORKSPACE_ROOT) / "backend/app/services/url_service.py"
    assert written_file.exists()
    assert written_file.read_text() == artifact["content"]


def test_multi_file_generation_creates_one_artifact_per_file(client):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(raw_payload=MULTI_FILE_ARTIFACT_GENERATION)

    response = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts")
    assert response.status_code == 201
    artifacts = response.json()
    assert len(artifacts) == 2
    assert {a["artifact_type"] for a in artifacts} == {"SOURCE_CODE", "TEST"}


def test_unsafe_relative_path_traversal_is_rejected_and_not_persisted(client):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(raw_payload=UNSAFE_PATH_ARTIFACT_GENERATION)

    response = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts")
    assert response.status_code == 422

    task_response = client.get("/api/v1/tasks/TASK-000001/artifacts")
    assert task_response.json() == []


def test_unsafe_absolute_path_is_rejected(client):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(raw_payload=UNSAFE_ABSOLUTE_PATH_ARTIFACT_GENERATION)

    response = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts")
    assert response.status_code == 422


def test_ai_provider_failure_returns_503(client):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(error=AIProviderError("simulated timeout"))

    response = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts")
    assert response.status_code == 503


def test_invalid_artifact_output_returns_502(client):
    ai_run_id = _create_accepted_ai_run(client)
    bad_payload = {
        "artifacts": [
            {"artifact_type": "NOT_REAL", "path": "x", "content": "", "description": ""}
        ]
    }
    _override_ai_provider(raw_payload=bad_payload)

    response = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts")
    assert response.status_code == 502


def test_get_unknown_artifact_returns_404(client):
    response = client.get("/api/v1/artifacts/ARTIFACT-999999")
    assert response.status_code == 404


def test_get_task_artifacts_for_unknown_task_returns_404(client):
    response = client.get("/api/v1/tasks/TASK-999999/artifacts")
    assert response.status_code == 404


def test_versioning_on_regeneration_supersedes_prior_and_preserves_it(client):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(raw_payload=VALID_ARTIFACT_GENERATION)
    first = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts").json()[0]

    _override_ai_provider(raw_payload=REVISED_ARTIFACT_GENERATION)
    second = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts").json()[0]

    assert first["id"] != second["id"]
    assert first["version"] == 1
    assert second["version"] == 2
    assert second["supersedes_artifact_id"] == first["id"]
    assert second["diff"] is not None
    assert "v2: retry loop added" in second["diff"]

    # The original artifact must still exist, content untouched.
    original = client.get(f"/api/v1/artifacts/{first['id']}").json()
    assert "v2" not in original["content"]

    task_artifacts = client.get(f"/api/v1/tasks/{original['task_id']}/artifacts").json()
    assert len(task_artifacts) == 2


def test_artifact_decision_accept(client):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(raw_payload=VALID_ARTIFACT_GENERATION)
    artifact = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts").json()[0]

    response = client.post(
        f"/api/v1/artifacts/{artifact['id']}/decision",
        json={"decision": "ACCEPT", "rationale": "Matches the approach."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "APPROVED"
    assert body["decisions"][0]["decision"] == "ACCEPT"


def test_artifact_decision_reject_requires_rationale(client):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(raw_payload=VALID_ARTIFACT_GENERATION)
    artifact = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts").json()[0]

    missing = client.post(
        f"/api/v1/artifacts/{artifact['id']}/decision", json={"decision": "REJECT"}
    )
    assert missing.status_code == 422

    response = client.post(
        f"/api/v1/artifacts/{artifact['id']}/decision",
        json={"decision": "REJECT", "rationale": "Not aligned with schema."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_decision_on_unknown_artifact_returns_404(client):
    response = client.post(
        "/api/v1/artifacts/ARTIFACT-999999/decision", json={"decision": "ACCEPT"}
    )
    assert response.status_code == 404


def test_traceability_task_to_ai_run_to_artifact(client):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(raw_payload=VALID_ARTIFACT_GENERATION)
    artifact = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts").json()[0]

    assert artifact["ai_run_id"] == ai_run_id
    task_artifacts = client.get(f"/api/v1/tasks/{artifact['task_id']}/artifacts").json()
    assert artifact["id"] in [a["id"] for a in task_artifacts]


def test_persistence_failure_on_generation_returns_500_with_no_internal_detail(client, monkeypatch):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(raw_payload=VALID_ARTIFACT_GENERATION)

    def _broken_save_artifacts(*args, **kwargs):
        raise PersistenceError("simulated database outage: connection refused at 10.0.0.5:5432")

    monkeypatch.setattr(artifact_repository, "save_artifacts", _broken_save_artifacts)

    response = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts")
    assert response.status_code == 500
    assert "10.0.0.5" not in response.text
    assert "Traceback" not in response.text


def test_persistence_failure_on_decision_returns_500_with_no_internal_detail(client, monkeypatch):
    ai_run_id = _create_accepted_ai_run(client)
    _override_ai_provider(raw_payload=VALID_ARTIFACT_GENERATION)
    artifact = client.post(f"/api/v1/ai-runs/{ai_run_id}/artifacts").json()[0]

    def _broken_save_decision(*args, **kwargs):
        raise PersistenceError("simulated database outage")

    monkeypatch.setattr(artifact_repository, "save_artifact_decision", _broken_save_decision)

    response = client.post(
        f"/api/v1/artifacts/{artifact['id']}/decision", json={"decision": "ACCEPT"}
    )
    assert response.status_code == 500
