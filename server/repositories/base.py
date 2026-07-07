"""Base repository for SQLite persistence."""

from __future__ import annotations

from typing import Any

import aiosqlite

from db import Database


class BaseRepository:
    """Base class for SQLite-backed repositories."""

    def __init__(self, database: Database) -> None:
        self._database = database

    @property
    def _db(self) -> Database:
        """Return the underlying Database instance."""
        return self._database

    async def _execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> aiosqlite.Cursor:
        """Execute a SQL statement and return the cursor."""
        cursor = await self._database.execute(sql, parameters)
        await self._database.commit()
        return cursor
