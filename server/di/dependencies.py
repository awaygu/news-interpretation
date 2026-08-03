"""FastAPI dependency injection accessors."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from config.dependencies import get_settings
from db import Database
from di.container import AppContainer
from di.state import AppState
from repositories.news import NewsRepository
from services.news import NewsService


def get_app(request: Request) -> Any:
    """Return the FastAPI application instance."""
    return request.app


def get_container(request: Request) -> AppContainer:
    """Return the application dependency container."""
    return request.app.state.container


def get_settings_dependency() -> Any:
    """Return cached application settings.

    This wrapper exists so callers can either use ``Depends(get_settings)``
    from ``config.dependencies`` or ``Depends(get_settings_dependency)`` here.
    """
    return get_settings()


def get_database(request: Request) -> Database:
    """Return the application database connection manager."""
    return request.app.state.container.database


def get_app_state(request: Request) -> AppState:
    """Return the mutable application runtime state."""
    return request.app.state.container.state


def get_news_repository(request: Request) -> NewsRepository:
    """Return the news repository."""
    return request.app.state.container.news_repo


def get_news_service(request: Request) -> NewsService:
    """Return the news domain service."""
    return request.app.state.container.news_service


__all__ = [
    "get_app",
    "get_container",
    "get_settings_dependency",
    "get_database",
    "get_app_state",
    "get_news_repository",
]
