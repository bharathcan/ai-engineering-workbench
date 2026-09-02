from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, sourced from environment variables.

    Every field is optional with a safe default so the application can
    start with no external services and no AI credentials configured.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str | None = None
    redis_url: str | None = None

    ai_provider: str | None = None
    ai_api_key: str | None = None
    ai_model: str | None = None

    # Salt for hashing client IPs before storing them (see
    # app.services.click_analytics and ADR-005) — never the raw IP. If
    # unset, a random salt is generated at process startup instead of
    # falling back to a hardcoded value, which would make the hash
    # trivially reversible via a precomputed table over common IP ranges.
    # Trade-off: without a configured, persistent salt, repeat-visitor
    # detection resets across restarts — documented, not hidden.
    ip_hash_salt: str | None = None


settings = Settings()
