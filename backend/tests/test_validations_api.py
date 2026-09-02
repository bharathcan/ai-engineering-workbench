from app.api.deps import get_ai_provider_factory
from app.main import app
from tests.support.ai_recommendation_payloads import VALID_RECOMMENDATION
from tests.support.analysis_payloads import VALID_URL_SHORTENER_ANALYSIS
from tests.support.artifact_payloads import VALID_ARTIFACT_GENERATION
from tests.support.fake_ai_provider import FakeAIProvider
from tests.support.task_plan_payloads import VALID_URL_SHORTENER_PLAN

URL_SHORTENER_TEXT = "Build a scalable URL shortener service with APIs, persistence, and analytics."


def _override_ai_provider(**kwargs):
    app.dependency_overrides[get_ai_provider_factory] = lambda: (
        lambda: FakeAIProvider(**kwargs)
    )


def _create_artifact(client) -> str:
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

    _override_ai_provider(raw_payload=VALID_ARTIFACT_GENERATION)
    artifact = client.post(f"/api/v1/ai-runs/{run['id']}/artifacts").json()[0]
    return artifact["id"]


def test_validate_unknown_artifact_returns_404(client):
    response = client.post(
        "/api/v1/artifacts/ARTIFACT-999999/validate", json={"validation_type": "STATIC_ANALYSIS"}
    )
    assert response.status_code == 404


def test_validate_rejects_unsupported_validation_type(client):
    artifact_id = _create_artifact(client)
    response = client.post(
        f"/api/v1/artifacts/{artifact_id}/validate", json={"validation_type": "NOT_A_TYPE"}
    )
    assert response.status_code == 422


def test_validate_rejects_command_injection_attempts_in_validation_type(client):
    """Phase 12 security review (docs/security.md #4): validation_type is a
    closed enum at the schema level, never a raw command — there is no code
    path from this field into subprocess.run's arguments. Confirms that
    directly: shell-metacharacter payloads are rejected the same way any
    other unsupported string is (422, before reaching the validation
    runner), never executed."""
    artifact_id = _create_artifact(client)
    injection_attempts = [
        "STATIC_ANALYSIS; rm -rf /",
        "STATIC_ANALYSIS && cat /etc/passwd",
        "$(whoami)",
        "STATIC_ANALYSIS`id`",
        "../../etc/passwd",
    ]
    for payload in injection_attempts:
        response = client.post(
            f"/api/v1/artifacts/{artifact_id}/validate", json={"validation_type": payload}
        )
        assert response.status_code == 422, f"payload {payload!r} was not rejected"


def test_static_analysis_validation_actually_runs_and_passes(client):
    artifact_id = _create_artifact(client)
    response = client.post(
        f"/api/v1/artifacts/{artifact_id}/validate", json={"validation_type": "STATIC_ANALYSIS"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"].startswith("VALIDATION-")
    assert body["artifact_id"] == artifact_id
    assert body["validation_type"] == "STATIC_ANALYSIS"
    assert body["command"] == "ruff check ."
    assert body["status"] in ("PASSED", "FAILED")
    assert body["evidence"]


def test_api_contract_validation_passes(client):
    artifact_id = _create_artifact(client)
    response = client.post(
        f"/api/v1/artifacts/{artifact_id}/validate", json={"validation_type": "API_CONTRACT"}
    )
    assert response.status_code == 201
    assert response.json()["status"] == "PASSED"


def test_security_validation_passes_on_clean_content(client):
    artifact_id = _create_artifact(client)
    response = client.post(
        f"/api/v1/artifacts/{artifact_id}/validate", json={"validation_type": "SECURITY"}
    )
    assert response.status_code == 201
    assert response.json()["status"] == "PASSED"


def test_performance_validation_is_not_validated(client):
    artifact_id = _create_artifact(client)
    response = client.post(
        f"/api/v1/artifacts/{artifact_id}/validate", json={"validation_type": "PERFORMANCE"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "NOT_VALIDATED"
    assert body["error"]


def test_multiple_validations_are_all_persisted_and_listed(client):
    artifact_id = _create_artifact(client)
    base = f"/api/v1/artifacts/{artifact_id}/validate"
    client.post(base, json={"validation_type": "STATIC_ANALYSIS"})
    client.post(base, json={"validation_type": "API_CONTRACT"})
    client.post(base, json={"validation_type": "SECURITY"})

    response = client.get(f"/api/v1/artifacts/{artifact_id}/validations")
    assert response.status_code == 200
    validations = response.json()
    assert len(validations) == 3
    assert {v["validation_type"] for v in validations} == {
        "STATIC_ANALYSIS",
        "API_CONTRACT",
        "SECURITY",
    }


def test_get_validations_for_unknown_artifact_returns_404(client):
    response = client.get("/api/v1/artifacts/ARTIFACT-999999/validations")
    assert response.status_code == 404


def test_get_single_validation(client):
    artifact_id = _create_artifact(client)
    created = client.post(
        f"/api/v1/artifacts/{artifact_id}/validate", json={"validation_type": "SECURITY"}
    ).json()

    response = client.get(f"/api/v1/validations/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_unknown_validation_returns_404(client):
    response = client.get("/api/v1/validations/VALIDATION-999999")
    assert response.status_code == 404


def test_traceability_artifact_to_validation(client):
    artifact_id = _create_artifact(client)
    created = client.post(
        f"/api/v1/artifacts/{artifact_id}/validate", json={"validation_type": "STATIC_ANALYSIS"}
    ).json()

    assert created["artifact_id"] == artifact_id
    listed = client.get(f"/api/v1/artifacts/{artifact_id}/validations").json()
    assert created["id"] in [v["id"] for v in listed]
