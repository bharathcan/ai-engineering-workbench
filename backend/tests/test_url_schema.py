import pytest
from pydantic import ValidationError

from app.schemas.url import CreateUrlRequest


def test_valid_https_url_is_accepted():
    req = CreateUrlRequest(original_url="https://example.com/some/path?x=1")
    assert req.original_url == "https://example.com/some/path?x=1"


def test_valid_http_url_is_accepted():
    req = CreateUrlRequest(original_url="http://example.com")
    assert req.original_url == "http://example.com"


def test_empty_url_is_rejected():
    with pytest.raises(ValidationError):
        CreateUrlRequest(original_url="")


def test_whitespace_only_url_is_rejected():
    with pytest.raises(ValidationError):
        CreateUrlRequest(original_url="   ")


def test_url_over_max_length_is_rejected():
    long_url = "https://example.com/" + ("a" * 2100)
    with pytest.raises(ValidationError):
        CreateUrlRequest(original_url=long_url)


@pytest.mark.parametrize(
    "scheme_url",
    [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "ftp://example.com/file",
        "data:text/html,<script>alert(1)</script>",
    ],
)
def test_disallowed_scheme_is_rejected(scheme_url):
    with pytest.raises(ValidationError):
        CreateUrlRequest(original_url=scheme_url)


def test_url_without_host_is_rejected():
    with pytest.raises(ValidationError):
        CreateUrlRequest(original_url="https:///no-host")


def test_localhost_hostname_is_rejected():
    with pytest.raises(ValidationError):
        CreateUrlRequest(original_url="http://localhost/admin")


@pytest.mark.parametrize(
    "internal_ip_url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata endpoint
    ],
)
def test_private_or_internal_ip_literal_is_rejected(internal_ip_url):
    with pytest.raises(ValidationError):
        CreateUrlRequest(original_url=internal_ip_url)


def test_public_ip_literal_is_accepted():
    req = CreateUrlRequest(original_url="http://93.184.216.34/")
    assert req.original_url == "http://93.184.216.34/"
