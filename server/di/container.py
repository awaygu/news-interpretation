"""Application dependency container.

Aggregates settings, database, repositories, services, and runtime singletons.
The container is built once during application lifespan and stored on
``app.state.container``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import Settings
from db import Database
from di.state import AppState
from repositories.news import NewsRepository
from services.news import NewsService


@dataclass
class AppContainer:
    """Immutable container of application-level dependencies."""

    settings: Settings
    database: Database
    state: AppState
    news_repo: NewsRepository
    news_service: NewsService

    # Compatibility accessors mirror old ``deps.py`` names.
    @property
    def news_store(self) -> list[dict[str, Any]]:
        return self.state.news_store

    @property
    def article_store(self) -> list[dict[str, Any]]:
        return self.state.article_store

    @property
    def publish_log(self) -> list[dict[str, Any]]:
        return self.state.publish_log

    @property
    def news_lock(self) -> Any:
        return self.state.news_lock

    @property
    def article_lock(self) -> Any:
        return self.state.article_lock
