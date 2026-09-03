"""Coverage for DELETE /api/v1/requirements/{id} — added to support
cleaning up test/demo requirements without a database console. Exercises
the full cascade (requirement -> analysis, plan -> task -> ai_run ->
artifact -> validation, decisions at every review point) since no
ON DELETE CASCADE exists at the DB level (see
requirement_repository.delete_requirement's docstring) — this is the one
place that fan-out is actually walked and verified end to end."""

from app.api.deps import get_ai_provider_factory
from app.main import app
from tests.support.analysis_payloads import VALID_URL_SHORTENER_ANALYSIS
from tests.support.fake_ai_provider import FakeAIProvider
from tests.support.task_plan_payloads import VALID_URL_SHORTENER_PLAN
from tests.support.url_shortener_workbench_payloads import (
    CREATE_URL_ARTIFACT_GENERATION,
    CREATE_URL_RECOMMENDATION,
)

MANDATORY_REQUIREMENT = (
    "Build a scalable URL shortener service with APIs, persistence, and analytics."
)


def _override_ai_provider(**kwargs):
    app.dependency_overrides[get_ai_provider_factory] = lambda: (
        lambda: FakeAIProvider(**kwargs)
    )


def test_delete_unknown_requirement_returns_404(client):
    response = client.delete("/api/v1/requirements/REQ-999999")
    assert response.status_code == 404


def test_delete_requirement_with_no_plan_removes_it(client):
    created = client.post("/api/v1/requirements", json={"text": "Build a simple API."}).json()

    delete_response = client.delete(f"/api/v1/requirements/{created['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/requirements/{created['id']}")
    assert get_response.status_code == 404


def test_delete_requirement_cascades_through_full_pipeline(client):
    # Build the exact same full chain as
    # test_url_shortener_workbench_flow.py: requirement -> analysis ->
    # plan -> tasks (all decided) -> ai-run (decided) -> artifacts
    # (decided) -> validations. If cascading delete misses a table with a
    # foreign key back to any node in this chain, the DELETE call itself
    # will fail with an IntegrityError instead of the 204 asserted below.
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_ANALYSIS)
    requirement = client.post(
        "/api/v1/requirements", json={"text": MANDATORY_REQUIREMENT}
    ).json()
    client.post(f"/api/v1/requirements/{requirement['id']}/analyze")

    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)
    plan = client.post(f"/api/v1/requirements/{requirement['id']}/tasks").json()
    for task in plan["tasks"]:
        client.post(f"/api/v1/tasks/{task['id']}/decision", json={"decision": "ACCEPT"})

    create_url_task = next(
        t for t in plan["tasks"] if t["title"] == "Implement create-URL endpoint"
    )

    _override_ai_provider(raw_payload=CREATE_URL_RECOMMENDATION)
    ai_run = client.post(
        f"/api/v1/tasks/{create_url_task['id']}/ai-assist",
        json={"assistance_type": "CODE_GENERATION"},
    ).json()
    client.post(f"/api/v1/ai-runs/{ai_run['id']}/decision", json={"decision": "ACCEPT"})

    _override_ai_provider(raw_payload=CREATE_URL_ARTIFACT_GENERATION)
    artifacts = client.post(f"/api/v1/ai-runs/{ai_run['id']}/artifacts").json()
    for artifact in artifacts:
        client.post(f"/api/v1/artifacts/{artifact['id']}/decision", json={"decision": "ACCEPT"})

    source_artifact = next(a for a in artifacts if a["artifact_type"] == "SOURCE_CODE")
    client.post(
        f"/api/v1/artifacts/{source_artifact['id']}/validate",
        json={"validation_type": "STATIC_ANALYSIS"},
    )

    # --- The actual deletion under test ---
    delete_response = client.delete(f"/api/v1/requirements/{requirement['id']}")
    assert delete_response.status_code == 204

    assert client.get(f"/api/v1/requirements/{requirement['id']}").status_code == 404
    assert client.get(f"/api/v1/tasks/{create_url_task['id']}").status_code == 404
    assert client.get(f"/api/v1/artifacts/{source_artifact['id']}").status_code == 404


def test_delete_requirement_does_not_affect_other_requirements(client):
    keep = client.post("/api/v1/requirements", json={"text": "Keep this one."}).json()
    remove = client.post("/api/v1/requirements", json={"text": "Remove this one."}).json()

    delete_response = client.delete(f"/api/v1/requirements/{remove['id']}")
    assert delete_response.status_code == 204

    assert client.get(f"/api/v1/requirements/{keep['id']}").status_code == 200
    assert client.get(f"/api/v1/requirements/{remove['id']}").status_code == 404
