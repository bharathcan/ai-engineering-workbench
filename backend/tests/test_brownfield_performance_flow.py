"""Phase 9: the brownfield scenario ("The existing URL shortener has slow
redirect performance. Improve performance without changing the public
API.") processed through the workbench — analysis, plan, task review, and
AI assistance on the optimization task — mirroring the Phase 8 pattern.
See docs/scenarios/brownfield.md for the full narrative and real
before/after measurements (this test proves the process, not the numbers —
those come from a live server, not this in-process test)."""

from app.api.deps import get_ai_provider_factory
from app.main import app
from tests.support.brownfield_payloads import BROWNFIELD_ANALYSIS, BROWNFIELD_PLAN
from tests.support.fake_ai_provider import FakeAIProvider

BROWNFIELD_REQUIREMENT = (
    "The existing URL shortener has slow redirect performance. "
    "Improve performance without changing the public API."
)


def _override_ai_provider(**kwargs):
    app.dependency_overrides[get_ai_provider_factory] = lambda: (
        lambda: FakeAIProvider(**kwargs)
    )


def test_brownfield_requirement_processed_through_workbench_with_ai_assistance_preserved(client):
    _override_ai_provider(raw_payload=BROWNFIELD_ANALYSIS)
    create_response = client.post("/api/v1/requirements", json={"text": BROWNFIELD_REQUIREMENT})
    assert create_response.status_code == 201
    requirement = create_response.json()

    analyze_response = client.post(f"/api/v1/requirements/{requirement['id']}/analyze")
    analysis = analyze_response.json()["latest_analysis"]
    # The ambiguity ("slow" is unquantified) must be surfaced, not silently
    # assumed away.
    assert any(a["id"] == "AMB-001" for a in analysis["ambiguities"])
    # Redis must not be silently assumed as the answer — nothing in the
    # analysis or plan mentions it.
    assert "redis" not in str(analysis).lower()

    _override_ai_provider(raw_payload=BROWNFIELD_PLAN)
    plan_response = client.post(f"/api/v1/requirements/{requirement['id']}/tasks")
    plan = plan_response.json()
    assert plan["status"] == "GENERATED"
    assert [t["title"] for t in plan["tasks"]] == [
        "Analyze current redirect performance",
        "Identify the actual bottleneck",
        "Implement the optimization",
        "Regression test and re-measure",
    ]
    assert "redis" not in str(plan).lower()

    for task in plan["tasks"]:
        decision = client.post(f"/api/v1/tasks/{task['id']}/decision", json={"decision": "ACCEPT"})
        assert decision.status_code == 200

    implement_task = next(t for t in plan["tasks"] if t["title"] == "Implement the optimization")

    optimization_recommendation = {
        "summary": "Defer the click-count write off the redirect's critical path.",
        "approach": (
            "Split resolve_and_record_click into a read-only resolve step and a separate "
            "record_click_for step, and run the latter as a FastAPI BackgroundTask so it "
            "executes after the redirect response is already sent, not before."
        ),
        "files_to_change": [
            "backend/app/services/url_service.py",
            "backend/app/api/routes/urls.py",
        ],
        "proposed_changes": [
            "Add resolve_active_url() (SELECT only, no write).",
            "Add record_click_for() (the write, called separately).",
            "Add BackgroundTasks to the redirect route; schedule record_click_for after "
            "building the RedirectResponse.",
        ],
        "tests_to_add": [
            "test_redirect_response_contract_unchanged_after_phase_9_optimization",
        ],
        "risks": [
            "A click could be lost if the process crashes between responding and the "
            "background task completing — accepted as low-impact for a count/timestamp "
            "metric, not a durability-critical value.",
        ],
        "assumptions": [],
        "confidence": "MEDIUM",
    }
    _override_ai_provider(raw_payload=optimization_recommendation)
    ai_assist_response = client.post(
        f"/api/v1/tasks/{implement_task['id']}/ai-assist",
        json={"assistance_type": "CODE_GENERATION"},
    )
    assert ai_assist_response.status_code == 201
    ai_run = ai_assist_response.json()

    reject_response = client.post(
        f"/api/v1/ai-runs/{ai_run['id']}/decision",
        json={
            "decision": "MODIFY",
            "rationale": (
                "Approach is right, but must confirm response contract is pinned by a test."
            ),
            "changes": (
                "Add an explicit regression test asserting status/headers/body are unchanged."
            ),
        },
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["decisions"][0]["decision"] == "MODIFY"

    # A second AI run, addressing the feedback — this AND the original are
    # both preserved (never overwritten), same guarantee as Phase 5.
    revised_recommendation = {
        **optimization_recommendation,
        "tests_to_add": [
            *optimization_recommendation["tests_to_add"],
            "test_redirect_response_contract_unchanged_after_phase_9_optimization (explicit "
            "status/header/body assertions)",
        ],
        "confidence": "HIGH",
    }
    _override_ai_provider(raw_payload=revised_recommendation)
    revision_response = client.post(
        f"/api/v1/tasks/{implement_task['id']}/ai-assist",
        json={"assistance_type": "CODE_GENERATION"},
    )
    assert revision_response.status_code == 201
    revised_run = revision_response.json()
    assert revised_run["revised_from_ai_run_id"] == ai_run["id"]

    accept_response = client.post(
        f"/api/v1/ai-runs/{revised_run['id']}/decision", json={"decision": "ACCEPT"}
    )
    assert accept_response.status_code == 200

    # Both AI runs remain, in order, on the task's history — nothing overwritten.
    final_task = client.get(f"/api/v1/tasks/{implement_task['id']}").json()
    run_ids = [r["id"] for r in final_task["ai_runs"]]
    assert run_ids == [ai_run["id"], revised_run["id"]]
