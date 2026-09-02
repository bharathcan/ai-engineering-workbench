from collections.abc import Callable

from app.ai.base import AIProvider
from app.ai.factory import get_ai_provider


def get_ai_provider_factory() -> Callable[[], AIProvider]:
    """Returns a zero-arg factory rather than an already-built AIProvider.

    Route dependencies are resolved by FastAPI before the route body runs,
    so if this returned a built provider directly, an unconfigured AI
    provider would fail *every* call to this route — including one for a
    requirement_id that doesn't exist, before the 404 check ever runs.
    Deferring construction lets the route check for that first.

    Also lets tests override this with a fake provider via
    app.dependency_overrides, without the route importing any concrete
    provider class.
    """
    return get_ai_provider
