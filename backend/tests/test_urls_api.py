from datetime import datetime, timedelta, timezone


def test_create_url_returns_201_with_short_code(client):
    response = client.post("/api/v1/urls", json={"original_url": "https://example.com/page"})
    assert response.status_code == 201
    body = response.json()
    assert body["id"].startswith("URL-")
    assert len(body["short_code"]) == 7
    assert body["original_url"] == "https://example.com/page"
    assert body["status"] == "ACTIVE"
    assert body["expires_at"] is None


def test_create_url_rejects_invalid_scheme(client):
    response = client.post("/api/v1/urls", json={"original_url": "javascript:alert(1)"})
    assert response.status_code == 422


def test_create_url_rejects_empty_url(client):
    response = client.post("/api/v1/urls", json={"original_url": ""})
    assert response.status_code == 422


def test_create_url_rejects_private_ip_target(client):
    response = client.post("/api/v1/urls", json={"original_url": "http://127.0.0.1/admin"})
    assert response.status_code == 422


def test_create_url_rejects_localhost_by_name(client):
    response = client.post("/api/v1/urls", json={"original_url": "http://localhost:8000/admin"})
    assert response.status_code == 422


def test_create_url_rejects_excessively_long_url(client):
    # Phase 12 security review (docs/security.md #2): MAX_URL_LENGTH is
    # enforced at the schema level (app/schemas/url.py) — confirm it's
    # actually reachable through the API, not just defined.
    too_long = "https://example.com/" + ("a" * 2048)
    response = client.post("/api/v1/urls", json={"original_url": too_long})
    assert response.status_code == 422


def test_redirect_for_valid_code_returns_307_with_location(client):
    create = client.post("/api/v1/urls", json={"original_url": "https://example.com/target"})
    short_code = create.json()["short_code"]

    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/target"


def test_redirect_for_unknown_code_returns_404(client):
    response = client.get("/DOESNOTEXIST", follow_redirects=False)
    assert response.status_code == 404


def test_redirect_for_expired_code_returns_410(client):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    create = client.post(
        "/api/v1/urls", json={"original_url": "https://example.com/expired", "expires_at": past}
    )
    short_code = create.json()["short_code"]

    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 410


def test_redirect_for_future_expiry_still_works(client):
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    create = client.post(
        "/api/v1/urls", json={"original_url": "https://example.com/future", "expires_at": future}
    )
    short_code = create.json()["short_code"]

    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307


def test_redirect_increments_click_count_and_updates_timestamp(client):
    create = client.post("/api/v1/urls", json={"original_url": "https://example.com/tracked"})
    short_code = create.json()["short_code"]

    before = client.get(f"/api/v1/urls/{short_code}/analytics").json()
    assert before["click_count"] == 0
    assert before["last_accessed_at"] is None

    client.get(f"/{short_code}", follow_redirects=False)
    client.get(f"/{short_code}", follow_redirects=False)

    after = client.get(f"/api/v1/urls/{short_code}/analytics").json()
    assert after["click_count"] == 2
    assert after["last_accessed_at"] is not None


def test_analytics_for_unknown_code_returns_404(client):
    response = client.get("/api/v1/urls/DOESNOTEXIST/analytics")
    assert response.status_code == 404


def test_many_creations_all_get_unique_codes(client):
    # Not a true concurrent-request test (no multithreading harness here —
    # see docs/validation/PHASE-8-SECURITY-REVIEW.md for that limitation),
    # but confirms the collision-retry path holds up across many sequential
    # creations against the real unique constraint.
    codes = set()
    for i in range(50):
        response = client.post("/api/v1/urls", json={"original_url": f"https://example.com/{i}"})
        assert response.status_code == 201
        codes.add(response.json()["short_code"])
    assert len(codes) == 50


def test_health_route_not_shadowed_by_redirect_catch_all(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_redirect_response_contract_unchanged_after_phase_9_optimization(client):
    """Phase 9 (docs/scenarios/brownfield.md) deferred the click-count write
    to a background task, without changing GET /{short_code}'s public
    response. This pins that contract explicitly: exact status code,
    exact Location header, empty body, and — because the click write now
    happens after the response — the click must still land by the time a
    caller checks analytics next, even though it's no longer synchronous
    with the redirect itself."""
    create = client.post("/api/v1/urls", json={"original_url": "https://example.com/contract"})
    short_code = create.json()["short_code"]

    response = client.get(f"/{short_code}", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/contract"
    assert response.content == b""

    analytics = client.get(f"/api/v1/urls/{short_code}/analytics").json()
    assert analytics["click_count"] == 1
    assert analytics["last_accessed_at"] is not None
