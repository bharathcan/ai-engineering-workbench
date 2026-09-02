"""Phase 8: the mandatory URL shortener requirement, processed end-to-end
THROUGH the workbench itself (Requirement Analyzer -> Task Decomposer ->
task review -> AI assistance -> engineer review -> artifact generation ->
artifact review -> validation) rather than appearing as a disconnected
application. This is the durable, re-runnable proof of that process — see
tests/support/url_shortener_workbench_payloads.py for why the AI content
here is engineer-authored (no live AI provider is configured anywhere in
this environment)."""

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


def test_url_shortener_requirement_processed_through_the_full_workbench_pipeline(client):
    # --- 8A: Requirement Analyzer ---------------------------------------
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_ANALYSIS)
    create_response = client.post("/api/v1/requirements", json={"text": MANDATORY_REQUIREMENT})
    assert create_response.status_code == 201
    requirement = create_response.json()
    assert requirement["text"] == MANDATORY_REQUIREMENT

    analyze_response = client.post(f"/api/v1/requirements/{requirement['id']}/analyze")
    assert analyze_response.status_code == 200
    analysis = analyze_response.json()["latest_analysis"]
    assert analysis["summary"]
    assert {fr["id"] for fr in analysis["functional_requirements"]} == {
        "FR-001",
        "FR-002",
        "FR-003",
    }
    assert any(a["id"] == "AMB-001" for a in analysis["ambiguities"])  # traffic volume unresolved

    # --- 8B: Task Decomposer + engineer review of the plan ---------------
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_PLAN)
    plan_response = client.post(f"/api/v1/requirements/{requirement['id']}/tasks")
    assert plan_response.status_code == 201
    plan = plan_response.json()
    assert plan["status"] == "GENERATED"
    assert len(plan["tasks"]) == 4

    for task in plan["tasks"]:
        # Definition of Done: every task carries requirement refs,
        # dependencies (possibly empty), acceptance criteria, and an AI
        # assistance type.
        assert len(task["requirement_refs"]) > 0
        assert isinstance(task["dependencies"], list)
        assert len(task["acceptance_criteria"]) > 0
        assert task["ai_assistance_type"]

        decision = client.post(f"/api/v1/tasks/{task['id']}/decision", json={"decision": "ACCEPT"})
        assert decision.status_code == 200
        assert decision.json()["status"] == "APPROVED"

    create_url_task = next(
        t for t in plan["tasks"] if t["title"] == "Implement create-URL endpoint"
    )

    # --- 8E (flagship demonstration): AI assistance on the create-URL task
    _override_ai_provider(raw_payload=CREATE_URL_RECOMMENDATION)
    ai_assist_response = client.post(
        f"/api/v1/tasks/{create_url_task['id']}/ai-assist",
        json={
            "assistance_type": "CODE_GENERATION",
            "instructions": "Implement short-code generation with collision handling.",
        },
    )
    assert ai_assist_response.status_code == 201
    ai_run = ai_assist_response.json()
    assert ai_run["response"]["confidence"] == "MEDIUM"
    assert "url_repository.py" in " ".join(ai_run["response"]["files_to_change"])

    accept_run = client.post(
        f"/api/v1/ai-runs/{ai_run['id']}/decision",
        json={"decision": "ACCEPT", "rationale": "Matches ADR-002's chosen strategy."},
    )
    assert accept_run.status_code == 200

    # --- Artifact generation + engineer review ----------------------------
    _override_ai_provider(raw_payload=CREATE_URL_ARTIFACT_GENERATION)
    artifacts_response = client.post(f"/api/v1/ai-runs/{ai_run['id']}/artifacts")
    assert artifacts_response.status_code == 201
    artifacts = artifacts_response.json()
    assert len(artifacts) == 2

    for artifact in artifacts:
        approve = client.post(
            f"/api/v1/artifacts/{artifact['id']}/decision",
            json={"decision": "ACCEPT", "rationale": "Matches the accepted recommendation."},
        )
        assert approve.status_code == 200
        assert approve.json()["status"] == "APPROVED"

    # --- Validation (Phase 7 engine, exercised against these real,
    # engineer-approved artifacts) -----------------------------------------
    source_artifact = next(a for a in artifacts if a["artifact_type"] == "SOURCE_CODE")
    static_check = client.post(
        f"/api/v1/artifacts/{source_artifact['id']}/validate",
        json={"validation_type": "STATIC_ANALYSIS"},
    )
    assert static_check.status_code == 201
    assert static_check.json()["status"] == "PASSED"

    security_check = client.post(
        f"/api/v1/artifacts/{source_artifact['id']}/validate", json={"validation_type": "SECURITY"}
    )
    assert security_check.status_code == 201
    assert security_check.json()["status"] == "PASSED"

    # --- Full traceability: Requirement -> Task -> AI Run -> Artifact ->
    # Validation, and Engineer Decision at every review point ---------------
    final_task = client.get(f"/api/v1/tasks/{create_url_task['id']}").json()
    assert final_task["status"] == "APPROVED"
    assert final_task["ai_runs"][0]["id"] == ai_run["id"]
    assert final_task["ai_runs"][0]["decisions"][0]["decision"] == "ACCEPT"

    task_artifacts = client.get(f"/api/v1/tasks/{create_url_task['id']}/artifacts").json()
    assert {a["id"] for a in task_artifacts} == {a["id"] for a in artifacts}
    for a in task_artifacts:
        assert a["ai_run_id"] == ai_run["id"]

    validations = client.get(f"/api/v1/artifacts/{source_artifact['id']}/validations").json()
    assert {v["validation_type"] for v in validations} == {"STATIC_ANALYSIS", "SECURITY"}
    assert all(v["status"] == "PASSED" for v in validations)
