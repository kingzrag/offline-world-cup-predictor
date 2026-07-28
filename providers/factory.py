"""
ProviderFactory — Central registry and resolver for football data providers.

SOLID Principle: Dependency Inversion
  High-level modules (services, scheduler) depend on FootballProvider interface.
  ProviderFactory resolves the concrete implementation without exposing it.

Usage:
    # Get the primary configured provider (uses DEFAULT_FOOTBALL_PROVIDER setting)
    provider = ProviderFactory.get_provider()

    # Get a specific named provider
    provider = ProviderFactory.get_provider("football_data")
    provider = ProviderFactory.get_provider("sportmonks")
    provider = ProviderFactory.get_provider("api_football")

    # Register a new custom provider
    ProviderFactory.register("my_provider", MyCustomProvider)

Configuration:
    Set DEFAULT_FOOTBALL_PROVIDER in .env to choose the primary provider.
    Defaults to "football_data".

    Available options: football_data | api_football | sportmonks
"""

from typing import Dict, Optional, Type

from providers.base import FootballProvider
from utils.config import settings
from utils.logger import logger


class ProviderFactory:
    """
    Registry and resolver for FootballProvider implementations.

    Maintains a registry mapping provider names to zero-argument factory callables
    (typically lambdas that read from settings). Instantiates providers lazily on
    first request and caches instances.
    """

    # Maps provider name → zero-argument callable returning a FootballProvider instance
    _registry: Dict[str, callable] = {}
    _instances: Dict[str, FootballProvider] = {}

    @classmethod
    def register(cls, name: str, factory_fn: callable) -> None:
        """
        Register a zero-argument factory callable for a provider.

        The factory_fn should return a fully-configured FootballProvider instance.
        It is called lazily the first time get_provider(name) is called.

        Args:
            name: Unique identifier for the provider (e.g. "football_data")
            factory_fn: A zero-argument callable that returns a FootballProvider instance.
                        Typically a lambda reading from settings, e.g.:
                        lambda: FootballDataProvider(api_key=settings.FOOTBALL_DATA_API_KEY)
        """
        cls._registry[name.lower()] = factory_fn
        logger.debug(f"ProviderFactory: Registered provider '{name}'")

    @classmethod
    def get_provider(cls, name: Optional[str] = None) -> FootballProvider:
        """
        Resolve and return a provider by name. Lazily instantiates on first call.

        Args:
            name: Provider name (e.g. "football_data", "sportmonks"). If None,
                  falls back to DEFAULT_FOOTBALL_PROVIDER setting or "football_data".

        Returns:
            An instantiated FootballProvider implementation.

        Raises:
            ValueError: If the provider name is not registered.
        """
        if name is None:
            name = getattr(settings, "DEFAULT_FOOTBALL_PROVIDER", "football_data")

        name = name.lower()

        # Return cached instance
        if name in cls._instances:
            return cls._instances[name]

        if name not in cls._registry:
            available = ", ".join(cls._registry.keys()) or "none registered"
            raise ValueError(
                f"ProviderFactory: Unknown provider '{name}'. "
                f"Available providers: {available}"
            )

        factory_fn = cls._registry[name]
        try:
            instance = factory_fn()
            if not isinstance(instance, FootballProvider):
                raise TypeError(
                    f"Factory for '{name}' returned {type(instance).__name__}, "
                    "expected a FootballProvider instance"
                )
            cls._instances[name] = instance
            logger.info(f"ProviderFactory: Instantiated provider '{name}' ({type(instance).__name__})")
            return instance
        except Exception as exc:
            raise RuntimeError(
                f"ProviderFactory: Failed to instantiate provider '{name}': {exc}"
            ) from exc

    @classmethod
    def list_providers(cls) -> Dict[str, str]:
        """
        Return a mapping of all registered provider names to their factory callable.

        Returns:
            Dict of {name: callable_repr}
        """
        return {name: repr(fn) for name, fn in cls._registry.items()}

    @classmethod
    def reset(cls) -> None:
        """
        Clear all cached provider instances. Useful for testing.
        """
        cls._instances.clear()
        logger.debug("ProviderFactory: Cleared provider instance cache")


# ── Auto-register all built-in providers ──────────────────────────────────────
# This runs at import time so all providers are available immediately.

def _register_builtin_providers() -> None:
    """Register all built-in football providers as factory callables."""
    from providers.football_data import FootballDataProvider
    from providers.api_football import APIFootballProvider
    from providers.sportmonks import SportMonksProvider

    # Each lambda resolves settings at instantiation time (not at import time)
    ProviderFactory.register(
        "football_data",
        lambda: FootballDataProvider(
            api_key=getattr(settings, "FOOTBALL_DATA_API_KEY", "")
        ),
    )
    ProviderFactory.register(
        "api_football",
        lambda: APIFootballProvider(),
    )
    ProviderFactory.register(
        "sportmonks",
        lambda: SportMonksProvider(),
    )

    logger.info(
        f"ProviderFactory: Registered {len(ProviderFactory._registry)} built-in providers: "
        + ", ".join(ProviderFactory._registry.keys())
    )


_register_builtin_providers()
