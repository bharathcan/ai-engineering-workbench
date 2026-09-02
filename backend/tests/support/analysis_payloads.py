"""Example structured-analysis payloads used across tests. These represent
what a real AI provider's tool-call output would look like — tests feed
them into FakeAIProvider so the rest of the stack (parsing, persistence,
API) is exercised the same way it would be with a real provider."""

VALID_URL_SHORTENER_ANALYSIS = {
    "summary": (
        "Build a URL shortener with APIs for creating and resolving short "
        "links, durable persistence, and usage analytics, with scalability "
        "considered in the design."
    ),
    "functional_requirements": [
        {"id": "FR-001", "description": "Create shortened URL mappings."},
        {"id": "FR-002", "description": "Resolve short URLs to their destination."},
        {"id": "FR-003", "description": "Provide analytics on URL usage."},
    ],
    "non_functional_requirements": [
        {"id": "NFR-001", "description": "The architecture must consider scalability."},
    ],
    "ambiguities": [
        {
            "id": "AMB-001",
            "description": "Expected request volume is not specified.",
            "why_it_matters": "The scalability architecture depends on expected traffic.",
            "impact": "MEDIUM",
            "information_needed": "Expected average and peak requests per second.",
        },
    ],
    "assumptions": [
        {
            "id": "ASM-001",
            "description": "URLs are assumed to be publicly accessible.",
            "reason": "The requirement does not specify authentication.",
            "impact": "Authentication requirements may change the API design.",
        },
    ],
    "constraints": [],
    "success_criteria": [
        {
            "id": "SC-001",
            "description": (
                "A submitted URL can be shortened and later resolved back to its destination."
            ),
        },
    ],
    "engineering_concerns": [
        {"id": "ENG-001", "description": "Short code collisions must be handled as usage grows."},
    ],
}

AMBIGUOUS_ANALYTICS_ANALYSIS = {
    "summary": "Improve an unspecified analytics capability.",
    "functional_requirements": [],
    "non_functional_requirements": [],
    "ambiguities": [
        {
            "id": "AMB-001",
            "description": (
                "It is not specified which analytics capability this refers to, "
                "or what 'improve' means (accuracy, new metrics, performance, UI)."
            ),
            "why_it_matters": (
                "Without knowing the current analytics implementation and the "
                "desired change, no concrete scope can be defined."
            ),
            "impact": "HIGH",
            "information_needed": (
                "Which analytics system, and the specific improvement desired."
            ),
        },
    ],
    "assumptions": [],
    "constraints": [],
    "success_criteria": [],
    "engineering_concerns": [],
}

MINIMAL_API_ANALYSIS = {
    "summary": "Build an API with no further specification of purpose or resources.",
    "functional_requirements": [
        {"id": "FR-001", "description": "Expose an API."},
    ],
    "non_functional_requirements": [],
    "ambiguities": [
        {
            "id": "AMB-001",
            "description": "The API's purpose, resources, and protocol are not specified.",
            "why_it_matters": "No endpoints or data model can be designed without this.",
            "impact": "HIGH",
            "information_needed": "What the API should do and what data it should expose.",
        },
    ],
    "assumptions": [],
    "constraints": [],
    "success_criteria": [],
    "engineering_concerns": [],
}
