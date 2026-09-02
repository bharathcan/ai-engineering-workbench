from app.api.deps import get_ai_provider_factory
from app.core.exceptions import AIProviderError
from app.main import app
from tests.support.analysis_payloads import VALID_URL_SHORTENER_ANALYSIS
from tests.support.fake_ai_provider import FakeAIProvider

URL_SHORTENER_REQUIREMENT_TEXT = (
    "Build a scalable URL shortener service with APIs, persistence, and analytics."
)


def _override_ai_provider(**kwargs):
    # get_ai_provider_factory returns a *factory*, not a provider instance
    # (see app.api.deps) — so the override must also be a callable that
    # returns a zero-arg callable that returns the fake provider.
    app.dependency_overrides[get_ai_provider_factory] = lambda: (
        lambda: FakeAIProvider(**kwargs)
    )


def test_create_requirement_returns_201_with_no_analysis_yet(client):
    response = client.post("/api/v1/requirements", json={"text": "Build an API."})

    assert response.status_code == 201
    body = response.json()
    assert body["id"].startswith("REQ-")
    assert body["text"] == "Build an API."
    assert body["status"] == "CREATED"
    assert body["latest_analysis"] is None


def test_create_requirement_rejects_empty_text(client):
    response = client.post("/api/v1/requirements", json={"text": ""})
    assert response.status_code == 422


def test_create_requirement_rejects_whitespace_only_text(client):
    response = client.post("/api/v1/requirements", json={"text": "   \n\t  "})
    assert response.status_code == 422


def test_get_unknown_requirement_returns_404(client):
    response = client.get("/api/v1/requirements/REQ-999999")
    assert response.status_code == 404


def test_analyze_unknown_requirement_returns_404(client):
    response = client.post("/api/v1/requirements/REQ-999999/analyze")
    assert response.status_code == 404


def test_full_flow_create_analyze_get(client):
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_ANALYSIS)

    create_response = client.post(
        "/api/v1/requirements",
        json={"text": URL_SHORTENER_REQUIREMENT_TEXT},
    )
    assert create_response.status_code == 201
    requirement_id = create_response.json()["id"]

    analyze_response = client.post(f"/api/v1/requirements/{requirement_id}/analyze")
    assert analyze_response.status_code == 200
    analyzed_body = analyze_response.json()
    assert analyzed_body["status"] == "ANALYZED"
    assert analyzed_body["latest_analysis"] is not None
    assert len(analyzed_body["latest_analysis"]["functional_requirements"]) == 3

    get_response = client.get(f"/api/v1/requirements/{requirement_id}")
    assert get_response.status_code == 200
    fetched_body = get_response.json()
    assert fetched_body["latest_analysis"] == analyzed_body["latest_analysis"]


def test_analyze_with_ai_provider_failure_returns_503_and_does_not_persist_analysis(client):
    _override_ai_provider(error=AIProviderError("simulated timeout"))

    create_response = client.post(
        "/api/v1/requirements", json={"text": "Build a scalable service."}
    )
    requirement_id = create_response.json()["id"]

    analyze_response = client.post(f"/api/v1/requirements/{requirement_id}/analyze")
    assert analyze_response.status_code == 503

    get_response = client.get(f"/api/v1/requirements/{requirement_id}")
    assert get_response.json()["status"] == "CREATED"
    assert get_response.json()["latest_analysis"] is None


def test_analyze_with_invalid_ai_output_returns_502_and_does_not_persist_analysis(client):
    _override_ai_provider(raw_payload={"summary": "incomplete, missing required fields"})

    create_response = client.post(
        "/api/v1/requirements", json={"text": "Build a scalable service."}
    )
    requirement_id = create_response.json()["id"]

    analyze_response = client.post(f"/api/v1/requirements/{requirement_id}/analyze")
    assert analyze_response.status_code == 502

    get_response = client.get(f"/api/v1/requirements/{requirement_id}")
    assert get_response.json()["status"] == "CREATED"
    assert get_response.json()["latest_analysis"] is None


def test_error_responses_do_not_leak_internal_details(client):
    _override_ai_provider(error=AIProviderError("secret internal detail: db-password=hunter2"))

    create_response = client.post(
        "/api/v1/requirements", json={"text": "Build a scalable service."}
    )
    requirement_id = create_response.json()["id"]

    analyze_response = client.post(f"/api/v1/requirements/{requirement_id}/analyze")
    assert "hunter2" not in analyze_response.text
    assert "Traceback" not in analyze_response.text


def test_list_requirements_returns_a_list(client):
    # This suite shares one test database across the whole session (see
    # tests/conftest.py) — other tests may have already created
    # requirements by the time this runs, so this only checks the shape,
    # not that the list starts empty.
    response = client.get("/api/v1/requirements")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_requirements_returns_newest_first(client):
    first = client.post("/api/v1/requirements", json={"text": "First requirement."}).json()
    second = client.post("/api/v1/requirements", json={"text": "Second requirement."}).json()

    body = client.get("/api/v1/requirements").json()
    ids = [r["id"] for r in body]
    # Relative order only — other tests may have added other requirements
    # to this shared database before or after these two.
    assert ids.index(second["id"]) < ids.index(first["id"])


def test_list_requirements_reflects_analysis_status(client):
    _override_ai_provider(raw_payload=VALID_URL_SHORTENER_ANALYSIS)
    created = client.post(
        "/api/v1/requirements", json={"text": URL_SHORTENER_REQUIREMENT_TEXT}
    ).json()
    client.post(f"/api/v1/requirements/{created['id']}/analyze")

    response = client.get("/api/v1/requirements")
    listed = next(r for r in response.json() if r["id"] == created["id"])
    assert listed["status"] == "ANALYZED"
    assert listed["latest_analysis"] is not None
