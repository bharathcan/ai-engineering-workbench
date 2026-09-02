"""Phase 10 (post-decision): the clarified requirement — after the engineer
chose Interpretation C (Advanced User Analytics) for the ambiguous
"Improve the analytics." scenario — processed through the same workbench
pipeline as Phases 8-9. Confirms the ambiguity gate that blocked the
*original* ambiguous requirement no longer blocks this clarified one (no
HIGH-impact ambiguity remains), and that AI assistance was used and
reviewed, not silently auto-implemented."""

from app.api.deps import get_ai_provider_factory
from app.main import app
from tests.support.advanced_analytics_payloads import (
    CLARIFIED_ANALYSIS,
    CLARIFIED_PLAN,
    CLARIFIED_REQUIREMENT_TEXT,
    CLICK_EVENT_RECOMMENDATION,
)
from tests.support.fake_ai_provider import FakeAIProvider


def _override_ai_provider(**kwargs):
    app.dependency_overrides[get_ai_provider_factory] = lambda: (
        lambda: FakeAIProvider(**kwargs)
    )


def test_clarified_requirement_unblocks_the_ambiguity_gate_and_ai_assistance_is_reviewed(client):
    _override_ai_provider(raw_payload=CLARIFIED_ANALYSIS)
    create_response = client.post(
        "/api/v1/requirements", json={"text": CLARIFIED_REQUIREMENT_TEXT}
    )
    assert create_response.status_code == 201
    requirement = create_response.json()

    analyze_response = client.post(f"/api/v1/requirements/{requirement['id']}/analyze")
    analysis = analyze_response.json()["latest_analysis"]
    # The clarified requirement still has an honest, low-impact ambiguity
    # (no GeoIP source) — but nothing HIGH, so it must not block planning.
    assert all(a["impact"] != "HIGH" for a in analysis["ambiguities"])

    _override_ai_provider(raw_payload=CLARIFIED_PLAN)
    plan_response = client.post(f"/api/v1/requirements/{requirement['id']}/tasks")
    assert plan_response.status_code == 201
    plan = plan_response.json()
    # Confirms the gate is genuinely about impact, not about this
    # requirement being related to "analytics" in general — the original
    # ambiguous version blocked (Phase 10 live demo); this one, with the
    # ambiguity resolved by an explicit engineer decision, does not.
    assert plan["status"] == "GENERATED"
    assert len(plan["tasks"]) == 2

    for task in plan["tasks"]:
        decision = client.post(f"/api/v1/tasks/{task['id']}/decision", json={"decision": "ACCEPT"})
        assert decision.status_code == 200

    click_event_task = next(
        t for t in plan["tasks"] if t["title"] == "Add ClickEvent model and hashed-IP capture"
    )

    _override_ai_provider(raw_payload=CLICK_EVENT_RECOMMENDATION)
    ai_assist_response = client.post(
        f"/api/v1/tasks/{click_event_task['id']}/ai-assist",
        json={"assistance_type": "CODE_GENERATION"},
    )
    assert ai_assist_response.status_code == 201
    ai_run = ai_assist_response.json()
    assert "ip_hash" in " ".join(ai_run["response"]["proposed_changes"]).lower()

    accept_response = client.post(
        f"/api/v1/ai-runs/{ai_run['id']}/decision",
        json={
            "decision": "ACCEPT",
            "rationale": "Matches ADR-005's privacy mitigations (hashed IP, no fabricated geo).",
        },
    )
    assert accept_response.status_code == 200

    final_task = client.get(f"/api/v1/tasks/{click_event_task['id']}").json()
    assert final_task["ai_runs"][0]["decisions"][0]["decision"] == "ACCEPT"
