"""News repository."""

from __future__ import annotations

import json
from typing import Any

from repositories.base import BaseRepository


class NewsRepository(BaseRepository):
    """Repository for news items persistence and retrieval."""

    async def save(self, items: list[dict[str, Any]]) -> None:
        """Replace all news with the given items."""
        await self._db.execute("DELETE FROM news")
        for item in items:
            extra_json = json.dumps(item.get("extra", {}), ensure_ascii=False)
            await self._db.execute(
                """
                INSERT OR REPLACE INTO news
                    (news_id, title, summary, content, source, url, published_at, extra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["news_id"],
                    item["title"],
                    item.get("summary", ""),
                    item.get("content", ""),
                    item.get("source", ""),
                    item.get("url", ""),
                    item.get("published_at", ""),
                    extra_json,
                ),
            )
        await self._db.commit()

    async def append(self, items: list[dict[str, Any]]) -> None:
        """Append news items, replacing existing ones by news_id."""
        for item in items:
            extra_json = json.dumps(item.get("extra", {}), ensure_ascii=False)
            await self._db.execute(
                """
                INSERT OR REPLACE INTO news
                    (news_id, title, summary, content, source, url, published_at, extra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["news_id"],
                    item["title"],
                    item.get("summary", ""),
                    item.get("content", ""),
                    item.get("source", ""),
                    item.get("url", ""),
                    item.get("published_at", ""),
                    extra_json,
                ),
            )
        await self._db.commit()

    async def upsert(self, items: list[dict[str, Any]]) -> int:
        """Insert only new news items, skipping existing news_ids.

        Returns the number of actually inserted items.
        """
        if not items:
            return 0
        inserted = 0
        for item in items:
            extra_json = json.dumps(item.get("extra", {}), ensure_ascii=False)
            cursor = await self._db.execute(
                """
                INSERT OR IGNORE INTO news
                    (news_id, title, summary, content, source, url, published_at, extra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["news_id"],
                    item["title"],
                    item.get("summary", ""),
                    item.get("content", ""),
                    item.get("source", ""),
                    item.get("url", ""),
                    item.get("published_at", ""),
                    extra_json,
                ),
            )
            inserted += cursor.rowcount
        await self._db.commit()
        return inserted

    async def update_content(self, news_id: str, content: str) -> None:
        """Update the content of a single news item."""
        await self._db.execute(
            "UPDATE news SET content = ? WHERE news_id = ?",
            (content, news_id),
        )
        await self._db.commit()

    async def clear_content_by_source(self, source: str) -> int:
        """Clear cached content for a source."""
        cursor = await self._db.execute(
            "UPDATE news SET content = '' WHERE source = ?",
            (source,),
        )
        await self._db.commit()
        return cursor.rowcount

    async def load(self) -> list[dict[str, Any]]:
        """Load all news ordered by published_at DESC."""
        cursor = await self._db.execute("SELECT * FROM news ORDER BY published_at DESC")
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            item = {
                "news_id": row["news_id"],
                "title": row["title"],
                "summary": row["summary"],
                "content": row["content"],
                "source": row["source"],
                "url": row["url"],
                "published_at": row["published_at"],
                "extra": json.loads(row["extra"]) if row["extra"] else {},
            }
            result.append(item)
        return result
