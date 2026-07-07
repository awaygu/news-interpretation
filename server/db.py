"""SQLite database connection manager.

Provides a reusable ``Database`` class that handles connection lifecycle,
WAL mode, and schema initialization. Legacy ``database.py`` functions delegate
here while the dependency-injection migration is in progress.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database wrapper.

    A single ``Database`` instance owns one connection. It is intended to live
    for the application lifespan and be shared by Repository instances.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> Database:
        """Open the connection and configure pragmas."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA busy_timeout=5000")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        logger.info("Database connected: %s", self.db_path)
        return self

    async def close(self) -> None:
        """Close the connection if open."""
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
            logger.info("Database closed: %s", self.db_path)

    @property
    def conn(self) -> aiosqlite.Connection:
        """Return the active connection."""
        if self._conn is None:
            raise RuntimeError("Database connection is not open")
        return self._conn

    async def execute(self, sql: str, parameters: tuple[Any, ...] | None = None) -> aiosqlite.Cursor:
        """Execute a SQL statement."""
        params = parameters or ()
        return await self.conn.execute(sql, params)

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.conn.commit()

    def __repr__(self) -> str:
        status = "open" if self._conn else "closed"
        return f"Database(db_path={self.db_path}, status={status})"
