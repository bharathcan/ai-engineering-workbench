"""Example task-decomposition payloads. VALID_URL_SHORTENER_PLAN's
requirement_refs deliberately match the ids in
tests/support/analysis_payloads.py::VALID_URL_SHORTENER_ANALYSIS, so the two
can be used together in an end-to-end test."""

VALID_URL_SHORTENER_PLAN = {
    "summary": (
        "Implement the URL shortener's core flows: persistence schema, "
        "create/redirect APIs, and basic analytics capture."
    ),
    "tasks": [
        {
            "id": "TASK-001",
            "title": "Define URL persistence schema",
            "description": (
                "Design the database schema for storing short-code-to-destination-URL mappings."
            ),
            "type": "DATABASE",
            "requirement_refs": ["FR-001", "FR-002"],
            "dependencies": [],
            "sequence": 1,
            "acceptance_criteria": [
                "Schema supports short code, destination URL, and creation timestamp.",
                "Schema reviewed by engineer.",
            ],
            "ai_assistance_type": "DESIGN",
            "risks": [],
        },
        {
            "id": "TASK-002",
            "title": "Implement create-URL endpoint",
            "description": (
                "Implement the API endpoint that accepts a destination URL "
                "and returns a short code."
            ),
            "type": "API",
            "requirement_refs": ["FR-001"],
            "dependencies": ["TASK-001"],
            "sequence": 2,
            "acceptance_criteria": [
                "Endpoint persists a new mapping.",
                "Endpoint returns the generated short code.",
            ],
            "ai_assistance_type": "CODE_GENERATION",
            "risks": [
                {
                    "id": "RISK-001",
                    "description": "Short code collisions as usage grows.",
                    "impact": "MEDIUM",
                },
            ],
        },
        {
            "id": "TASK-003",
            "title": "Implement redirect endpoint",
            "description": (
                "Implement the API endpoint that resolves a short code to its destination "
                "and redirects the caller."
            ),
            "type": "API",
            "requirement_refs": ["FR-002"],
            "dependencies": ["TASK-001"],
            "sequence": 2,
            "acceptance_criteria": [
                "Unknown short codes return a clear not-found error.",
                "Known short codes redirect to the destination URL.",
            ],
            "ai_assistance_type": "CODE_GENERATION",
            "risks": [],
        },
        {
            "id": "TASK-004",
            "title": "Add analytics capture",
            "description": "Record a usage event for each redirect, keyed by short code.",
            "type": "BACKEND",
            "requirement_refs": ["FR-003"],
            "dependencies": ["TASK-002", "TASK-003"],
            "sequence": 3,
            "acceptance_criteria": [
                "Each redirect increments a usage counter for its short code.",
            ],
            "ai_assistance_type": "CODE_GENERATION",
            "risks": [],
        },
    ],
    "assumptions": ["Tasks are grouped by API surface rather than by architectural layer."],
    "risks": [
        {
            "id": "RISK-002",
            "description": (
                "Expected traffic volume is unresolved (AMB-001), which may affect the "
                "persistence/caching approach chosen in TASK-001."
            ),
            "impact": "MEDIUM",
        },
    ],
}
