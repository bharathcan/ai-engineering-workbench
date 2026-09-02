class RequirementNotFoundError(Exception):
    def __init__(self, requirement_id: str):
        self.requirement_id = requirement_id
        super().__init__(f"Requirement '{requirement_id}' was not found.")


class AIProviderError(Exception):
    """Raised when the AI provider itself fails (timeout, network, rate limit, auth)."""


class InvalidAIResponseError(Exception):
    """Raised when the AI provider returns output that fails schema validation."""

    def __init__(self, message: str, raw_output: str | None = None):
        self.raw_output = raw_output
        super().__init__(message)


class PersistenceError(Exception):
    """Raised when a database operation fails unexpectedly."""


class RequirementNotAnalyzedError(Exception):
    """Raised when task decomposition is requested before the requirement has an analysis."""

    def __init__(self, requirement_id: str):
        self.requirement_id = requirement_id
        super().__init__(
            f"Requirement '{requirement_id}' has not been analyzed yet. "
            "Call POST /api/v1/requirements/{requirement_id}/analyze first."
        )


class EngineeringPlanNotFoundError(Exception):
    def __init__(self, requirement_id: str):
        self.requirement_id = requirement_id
        super().__init__(f"No engineering plan exists yet for requirement '{requirement_id}'.")


class TaskNotFoundError(Exception):
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task '{task_id}' was not found.")


class TaskNotApprovedError(Exception):
    """Raised when AI assistance is requested for a task that isn't APPROVED yet."""

    def __init__(self, task_id: str, current_status: str):
        self.task_id = task_id
        self.current_status = current_status
        super().__init__(
            f"Task '{task_id}' is not APPROVED (current status: {current_status}). "
            "Only approved tasks can receive AI assistance."
        )


class AIRunNotFoundError(Exception):
    def __init__(self, ai_run_id: str):
        self.ai_run_id = ai_run_id
        super().__init__(f"AI run '{ai_run_id}' was not found.")


class AIRunNotAcceptedError(Exception):
    """Raised when artifact generation is requested for an AI run whose
    recommendation was not ACCEPTed. Rejected (or not-yet-decided)
    recommendations must never become artifacts."""

    def __init__(self, ai_run_id: str, current_review_status: str):
        self.ai_run_id = ai_run_id
        self.current_review_status = current_review_status
        super().__init__(
            f"AI run '{ai_run_id}' has not been ACCEPTed (current review status: "
            f"{current_review_status}). Only an accepted recommendation can generate artifacts."
        )


class ArtifactNotFoundError(Exception):
    def __init__(self, artifact_id: str):
        self.artifact_id = artifact_id
        super().__init__(f"Artifact '{artifact_id}' was not found.")


class UnsafeArtifactPathError(Exception):
    """Raised when a proposed artifact path would write outside the
    approved generated/ workspace — see app.utils.safe_path."""


class ValidationNotFoundError(Exception):
    def __init__(self, validation_id: str):
        self.validation_id = validation_id
        super().__init__(f"Validation '{validation_id}' was not found.")


class UnsupportedValidationTypeError(Exception):
    """Raised for a validation_type with no allowlisted runner — see
    app.services.validation_runner.RUNNERS."""

    def __init__(self, validation_type: str):
        self.validation_type = validation_type
        super().__init__(f"No validation runner is registered for '{validation_type}'.")


class ShortCodeGenerationExhaustedError(Exception):
    """Raised when every collision-retry attempt produced an already-taken
    short code — see app.repositories.url_repository."""

    def __init__(self, attempts: int):
        self.attempts = attempts
        super().__init__(f"Failed to generate a unique short code after {attempts} attempts.")


class ShortenedUrlNotFoundError(Exception):
    def __init__(self, short_code: str):
        self.short_code = short_code
        super().__init__(f"Short code '{short_code}' was not found.")


class ShortenedUrlExpiredError(Exception):
    def __init__(self, short_code: str):
        self.short_code = short_code
        super().__init__(f"Short code '{short_code}' has expired.")
