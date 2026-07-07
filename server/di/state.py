"""Mutable application runtime state.

Holds in-memory stores, locks, and scheduler state. This object is attached to
``app.state.app_state`` and passed into services that need shared runtime state.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppState:
    """Mutable runtime state shared across requests."""

    news_store: list[dict[str, Any]] = field(default_factory=list)
    article_store: list[dict[str, Any]] = field(default_factory=list)
    publish_log: list[dict[str, Any]] = field(default_factory=list)

    news_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    article_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    schedule_running: bool = False
    newsnow_interval: int = 1800
    rss_interval: int = 1800
    last_newsnow_crawl: str | None = None
    last_rss_crawl: str | None = None
