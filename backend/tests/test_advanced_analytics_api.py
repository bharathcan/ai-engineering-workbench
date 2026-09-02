CHROME_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
SAFARI_IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


def test_advanced_analytics_for_unknown_code_returns_404(client):
    response = client.get("/api/v1/urls/DOESNOTEXIST/analytics/advanced")
    assert response.status_code == 404


def test_advanced_analytics_with_no_clicks_yet(client):
    create = client.post("/api/v1/urls", json={"original_url": "https://example.com/fresh"})
    short_code = create.json()["short_code"]

    response = client.get(f"/api/v1/urls/{short_code}/analytics/advanced")
    assert response.status_code == 200
    body = response.json()
    assert body["total_events"] == 0
    assert body["device_breakdown"] == []
    assert body["repeat_visitor_rate"] == 0.0
    assert body["geographic_breakdown"] == []
    assert "not" in body["geographic_status"].lower()


def test_redirect_captures_device_browser_and_referrer(client):
    create = client.post("/api/v1/urls", json={"original_url": "https://example.com/tracked"})
    short_code = create.json()["short_code"]

    client.get(
        f"/{short_code}",
        follow_redirects=False,
        headers={"User-Agent": CHROME_DESKTOP, "Referer": "https://news.example.com/article"},
    )
    client.get(
        f"/{short_code}",
        follow_redirects=False,
        headers={"User-Agent": SAFARI_IPHONE, "Referer": "https://social.example.com/post"},
    )

    response = client.get(f"/api/v1/urls/{short_code}/analytics/advanced")
    body = response.json()
    assert body["total_events"] == 2

    devices = {e["key"]: e["count"] for e in body["device_breakdown"]}
    assert devices == {"DESKTOP": 1, "MOBILE": 1}

    browsers = {e["key"]: e["count"] for e in body["browser_breakdown"]}
    assert browsers == {"CHROME": 1, "SAFARI": 1}

    referrers = {e["key"] for e in body["referrer_breakdown"]}
    assert referrers == {"https://news.example.com/article", "https://social.example.com/post"}


def test_redirect_with_no_headers_records_unknown_gracefully(client):
    create = client.post("/api/v1/urls", json={"original_url": "https://example.com/bare"})
    short_code = create.json()["short_code"]

    client.get(f"/{short_code}", follow_redirects=False)

    response = client.get(f"/api/v1/urls/{short_code}/analytics/advanced")
    body = response.json()
    assert body["total_events"] == 1
    referrers = {e["key"] for e in body["referrer_breakdown"]}
    assert referrers == {"(none)"}


def test_repeat_visitor_detected_via_hashed_ip_not_raw_ip(client):
    create = client.post("/api/v1/urls", json={"original_url": "https://example.com/repeat"})
    short_code = create.json()["short_code"]

    # TestClient requests all originate from the same test client "IP"
    # (testclient), so two redirects to the same code should register the
    # second as a repeat visit.
    client.get(f"/{short_code}", follow_redirects=False)
    client.get(f"/{short_code}", follow_redirects=False)

    response = client.get(f"/api/v1/urls/{short_code}/analytics/advanced")
    body = response.json()
    assert body["total_events"] == 2
    assert body["repeat_visitor_count"] == 1
    assert body["repeat_visitor_rate"] == 0.5


def test_advanced_analytics_never_exposes_raw_ip_or_full_user_agent_string_as_pii_field(client):
    """Structural check: the response schema has no ip/ip_address field at
    all — see ADR-005. (user_agent breakdown is intentionally reduced to
    browser/device categories, not the raw string, for the same reason.)"""
    create = client.post("/api/v1/urls", json={"original_url": "https://example.com/privacy"})
    short_code = create.json()["short_code"]
    client.get(f"/{short_code}", follow_redirects=False, headers={"User-Agent": CHROME_DESKTOP})

    response = client.get(f"/api/v1/urls/{short_code}/analytics/advanced")
    body = response.json()
    body_str = str(body).lower()
    assert "ip_hash" not in body_str
    assert "ip_address" not in body_str
