"""Example artifact-generation payloads for artifact-generation tests."""

VALID_ARTIFACT_GENERATION = {
    "artifacts": [
        {
            "artifact_type": "SOURCE_CODE",
            "path": "backend/app/services/url_service.py",
            "content": "def create_short_url(destination_url: str) -> str:\n    ...\n",
            "description": (
                "Adds a uniqueness constraint check with retry handling for short code "
                "collisions."
            ),
        },
    ],
}

REVISED_ARTIFACT_GENERATION = {
    "artifacts": [
        {
            "artifact_type": "SOURCE_CODE",
            "path": "backend/app/services/url_service.py",
            "content": (
                "def create_short_url(destination_url: str) -> str:\n"
                "    # v2: retry loop added\n    ...\n"
            ),
            "description": "Revised: adds a bounded retry loop on collision.",
        },
    ],
}

MULTI_FILE_ARTIFACT_GENERATION = {
    "artifacts": [
        {
            "artifact_type": "SOURCE_CODE",
            "path": "backend/app/services/url_service.py",
            "content": "def create_short_url(destination_url: str) -> str:\n    ...\n",
            "description": "Implementation.",
        },
        {
            "artifact_type": "TEST",
            "path": "backend/tests/test_url_service.py",
            "content": "def test_create_short_url():\n    assert True\n",
            "description": "Basic test.",
        },
    ],
}

UNSAFE_PATH_ARTIFACT_GENERATION = {
    "artifacts": [
        {
            "artifact_type": "CONFIGURATION",
            "path": "../../.env",
            "content": "SECRET_KEY=leaked",
            "description": "malicious path traversal attempt",
        },
    ],
}

UNSAFE_ABSOLUTE_PATH_ARTIFACT_GENERATION = {
    "artifacts": [
        {
            "artifact_type": "CONFIGURATION",
            "path": "/etc/passwd",
            "content": "root:x:0:0",
            "description": "malicious absolute path attempt",
        },
    ],
}
