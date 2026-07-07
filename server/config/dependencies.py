"""FastAPI dependency functions for configuration."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Request

from .settings import Settings


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings.

    The settings instance is built once per process. Tests can override this
    via ``app.dependency_overrides[get_settings] = lambda: Settings(...)``.
    """
    return Settings()


def get_settings_from_request(request: Request) -> Settings:
    """Return settings attached to the FastAPI app state."""
    return request.app.state.settings
