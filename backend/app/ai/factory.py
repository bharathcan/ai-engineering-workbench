from app.ai.base import AIProvider
from app.core.config import Settings
from app.core.config import settings as default_settings
from app.core.exceptions import AIProviderError


def get_ai_provider(config: Settings | None = None) -> AIProvider:
    """Build the configured AIProvider. The caller never picks a provider class directly."""
    config = config or default_settings
    provider_name = (config.ai_provider or "").strip().lower()

    if provider_name == "anthropic":
        if not config.ai_api_key:
            raise AIProviderError("AI_API_KEY is not configured for provider 'anthropic'.")
        from app.ai.anthropic_provider import AnthropicProvider

        model = config.ai_model or "claude-sonnet-5"
        return AnthropicProvider(api_key=config.ai_api_key, model=model)

    raise AIProviderError(
        f"No usable AI provider is configured (AI_PROVIDER={config.ai_provider!r}). "
        "Set AI_PROVIDER=anthropic and AI_API_KEY to enable requirement analysis."
    )
