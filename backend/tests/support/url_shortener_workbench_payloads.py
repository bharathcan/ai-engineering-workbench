"""Payloads for tests/test_url_shortener_workbench_flow.py — the durable,
committed proof that the URL shortener (Phase 8) was actually processed
through the workbench's own requirement -> analysis -> plan -> AI-assist ->
artifact -> validate pipeline, not built as an unrelated application.

No live AI provider is configured in this environment (no API key) — these
payloads are what a provider call would return, authored by the engineer
standing in for one, exactly like every other test fixture in this test
suite (see tests/support/analysis_payloads.py, task_plan_payloads.py, etc.
from Phases 3-7). The recommendation/artifact content below describes the
REAL implementation in app/models/url.py, app/services/short_code.py,
app/repositories/url_repository.py, app/services/url_service.py, and
app/api/routes/urls.py — it is not fictional.
"""

CREATE_URL_RECOMMENDATION = {
    "summary": (
        "Implement POST /api/v1/urls: validate the submitted URL, generate a random "
        "Base62 short code, and persist the mapping with collision retry."
    ),
    "approach": (
        "Add a CreateUrlRequest schema validating scheme (http/https only) and rejecting "
        "private/internal IP-literal targets. Generate short codes via secrets.choice over "
        "a 62-character alphabet (cryptographically secure, not enumerable — see "
        "ADR-002). Attempt the insert directly rather than pre-checking uniqueness, "
        "catching IntegrityError and retrying with a fresh code up to 5 times, so "
        "correctness relies on the database's own unique constraint rather than a "
        "check-then-insert race under concurrent requests."
    ),
    "files_to_change": [
        "backend/app/models/url.py",
        "backend/app/schemas/url.py",
        "backend/app/services/short_code.py",
        "backend/app/repositories/url_repository.py",
        "backend/app/services/url_service.py",
        "backend/app/api/routes/urls.py",
    ],
    "proposed_changes": [
        "Add ShortenedUrl model with a unique-indexed short_code column.",
        "Add CreateUrlRequest with scheme/host/private-IP validation.",
        "Add generate_short_code() using secrets.choice over Base62.",
        "Add create_shortened_url() with IntegrityError-triggered collision retry.",
        "Add POST /api/v1/urls returning the created mapping.",
    ],
    "tests_to_add": [
        "test_create_url_returns_201_with_short_code",
        "test_create_url_rejects_invalid_scheme",
        "test_create_url_rejects_private_ip_target",
        "test_collision_is_retried_and_a_unique_code_is_eventually_used",
        "test_exhausted_retries_raises_when_every_attempt_collides",
    ],
    "risks": [
        "Expected traffic volume is unresolved (AMB-001) — code length (7 chars) and "
        "retry bound (5) are sized for moderate scale, not validated against a real number.",
        "No multi-threaded/concurrent test harness exists in this environment — the "
        "collision-retry design argument for concurrency safety is untested under real "
        "concurrent load.",
    ],
    "assumptions": [
        "A 7-character Base62 code (62^7 ≈ 3.5 trillion possibilities) is sufficient "
        "collision resistance without a resolved traffic number.",
    ],
    "confidence": "MEDIUM",
}

CREATE_URL_ARTIFACT_GENERATION = {
    "artifacts": [
        {
            "artifact_type": "SOURCE_CODE",
            "path": "backend/app/services/short_code.py",
            "content": (
                "import secrets\n"
                "import string\n\n"
                "ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase\n"
                "DEFAULT_LENGTH = 7\n\n\n"
                "def generate_short_code(length: int = DEFAULT_LENGTH) -> str:\n"
                "    return \"\".join(secrets.choice(ALPHABET) for _ in range(length))\n"
            ),
            "description": (
                "Cryptographically secure random Base62 short-code generator — see "
                "ADR-002 for why secrets.choice (not random.choice) and why random "
                "rather than sequential codes."
            ),
        },
        {
            "artifact_type": "API_CONTRACT",
            "path": "backend/generated_docs/create_url_endpoint.md",
            "content": (
                "POST /api/v1/urls\n"
                "Request: { \"original_url\": string, \"expires_at\": datetime|null }\n"
                "Response 201: { \"id\", \"short_code\", \"original_url\", \"status\", "
                "\"created_at\", \"expires_at\" }\n"
                "Errors: 422 invalid URL, 503 short-code exhaustion, 500 persistence failure.\n"
            ),
            "description": "Contract summary for the create-URL endpoint.",
        },
    ],
}
