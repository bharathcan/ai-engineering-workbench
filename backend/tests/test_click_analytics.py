from app.services.click_analytics import hash_ip


def test_hash_ip_returns_none_for_none():
    assert hash_ip(None) is None


def test_hash_ip_returns_none_for_empty_string():
    assert hash_ip("") is None


def test_hash_ip_is_deterministic_for_same_input():
    assert hash_ip("203.0.113.42") == hash_ip("203.0.113.42")


def test_hash_ip_differs_for_different_inputs():
    assert hash_ip("203.0.113.42") != hash_ip("203.0.113.43")


def test_hash_ip_never_contains_the_raw_ip():
    result = hash_ip("203.0.113.42")
    assert result is not None
    assert "203.0.113.42" not in result
    # SHA-256 hex digest length.
    assert len(result) == 64
