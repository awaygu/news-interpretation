"""News domain service.

Encapsulates news ingestion, retrieval, and cache management. During the
migration this service still uses a few helpers from ``api.deps`` for content
fetching; they will be extracted into dedicated services in later phases.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from api import deps
from config import NEWS_SOURCES
from db import Database
from di.state import AppState
from repositories.news import NewsRepository
from sources import DEFAULT_RSS_FEEDS, NewsNowBatchCrawler, RSSBatchCrawler
from sources.filter import KeywordFilter

logger = logging.getLogger(__name__)


class NewsService:
    """Service for news aggregation and caching."""

    def __init__(
        self,
        state: AppState,
        database: Database,
        news_repo: NewsRepository,
        newsnow_batch: NewsNowBatchCrawler,
        rss_batch: RSSBatchCrawler,
        keyword_filter: KeywordFilter,
    ) -> None:
        self._state = state
        self._database = database
        self._news_repo = news_repo
        self._newsnow_batch = newsnow_batch
        self._rss_batch = rss_batch
        self._keyword_filter = keyword_filter

    def list_news(
        self,
        source: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Return a paginated list of news items."""
        pool = [n for n in self._state.news_store if n["source"] == source] if source else list(self._state.news_store)
        pool.sort(key=lambda n: n.get("published_at", ""), reverse=True)
        total = len(pool)
        items = pool[offset : offset + limit]
        return {"total": total, "offset": offset, "limit": limit, "items": items}

    def find_news(self, news_id: str) -> dict[str, Any] | None:
        """Find a single news item by id."""
        return deps.find_news(news_id)

    async def refresh_all(self) -> dict[str, Any]:
        """Re-crawl all NewsNow and RSS sources and merge into the store."""
        async with self._state.news_lock:
            existing_ids = {n["news_id"] for n in self._state.news_store}
            results: dict[str, Any] = {}
            all_raw: list[Any] = []

            try:
                newsnow_results = await self._newsnow_batch.crawl_all()
                for platform_id, items in newsnow_results.items():
                    all_raw.extend(items)
                    results[f"newsnow_{platform_id}"] = {"status": "ok", "count": len(items)}
                    logger.info("  ✓ NewsNow-%s: %d items", platform_id, len(items))
            except Exception as e:
                results["newsnow"] = {"status": "error", "error": str(e)}
                logger.warning("  ✗ NewsNow: %s", e)

            try:
                rss_results = await self._rss_batch.crawl_all()
                for feed_id, items in rss_results.items():
                    all_raw.extend(items)
                    results[f"rss_{feed_id}"] = {"status": "ok", "count": len(items)}
                    logger.info("  ✓ RSS-%s: %d items", feed_id, len(items))
            except Exception as e:
                results["rss"] = {"status": "error", "error": str(e)}
                logger.warning("  ✗ RSS: %s", e)

            filtered = self._keyword_filter.filter_newsitems(all_raw)
            new_count = 0
            new_items = []
            for item in filtered:
                d = item.to_dict()
                if d["news_id"] not in existing_ids:
                    self._state.news_store.append(d)
                    existing_ids.add(d["news_id"])
                    new_items.append(d)
                    new_count += 1

            if new_items:
                await self._news_repo.upsert(new_items)

        return {"total": len(self._state.news_store), "new": new_count, "total_raw": len(all_raw), "results": results}

    async def refresh_newsnow(self) -> dict[str, Any]:
        """Re-crawl all NewsNow platforms."""
        async with self._state.news_lock:
            results = await self._newsnow_batch.crawl_all()
            all_raw: list[Any] = []
            summary = {}

            for alias, items in results.items():
                all_raw.extend(items)
                summary[alias] = {"total": len(items)}
                logger.info("  ✓ %s: %d items", alias, len(items))

            filtered = self._keyword_filter.filter_newsitems(all_raw)
            new_items = []
            for item in filtered:
                item_dict = item.to_dict()
                existing = any(n["news_id"] == item_dict["news_id"] for n in self._state.news_store)
                if not existing:
                    self._state.news_store.append(item_dict)
                    new_items.append(item_dict)

            if new_items:
                await self._news_repo.upsert(new_items)

        return {
            "total_new": len(new_items),
            "total_raw": len(all_raw),
            "total_filtered": len(filtered),
            "summary": summary,
        }

    async def refresh_rss(self) -> dict[str, Any]:
        """Re-crawl all RSS feeds."""
        async with self._state.news_lock:
            results = await self._rss_batch.crawl_all()
            all_raw: list[Any] = []
            summary = {}

            for feed_id, items in results.items():
                all_raw.extend(items)
                summary[feed_id] = {"total": len(items)}
                logger.info("  ✓ RSS %s: %d items", feed_id, len(items))

            filtered = self._keyword_filter.filter_newsitems(all_raw)
            new_items = []
            for item in filtered:
                item_dict = item.to_dict()
                existing = any(n["news_id"] == item_dict["news_id"] for n in self._state.news_store)
                if not existing:
                    self._state.news_store.append(item_dict)
                    new_items.append(item_dict)

            if new_items:
                await self._news_repo.upsert(new_items)

        return {
            "total_new": len(new_items),
            "total_raw": len(all_raw),
            "total_filtered": len(filtered),
            "summary": summary,
        }

    async def refresh_source(self, source: str) -> dict[str, Any]:
        """Start a background refresh for a single source."""
        from sources.rss import RSSCrawler

        if source in deps.NEWSNOW_CRAWLERS:
            crawler = deps.NEWSNOW_CRAWLERS[source]
        elif any(feed.id == source for feed in DEFAULT_RSS_FEEDS):
            feed = next(f for f in DEFAULT_RSS_FEEDS if f.id == source)
            crawler = RSSCrawler(feed)
        else:
            raise ValueError(f"Unknown source: {source}")

        asyncio.create_task(self._bg_crawl_and_save(source, crawler))
        return {"source": source, "status": "refreshing"}

    async def refresh_newsnow_platform(self, platform_id: str) -> dict[str, Any]:
        """Start a background refresh for a single NewsNow platform."""
        if platform_id not in deps.NEWSNOW_CRAWLERS:
            raise ValueError(
                f"Unknown platform: {platform_id}. Available: {list(deps.NEWSNOW_CRAWLERS.keys())}"
            )

        crawler = deps.NEWSNOW_CRAWLERS[platform_id]
        asyncio.create_task(self._bg_crawl_and_save(platform_id, crawler))
        return {"platform": platform_id, "name": crawler.platform_name, "status": "refreshing"}

    async def clear_content_cache(self, source: str) -> dict[str, Any]:
        """Clear cached content for a source."""
        if source not in NEWS_SOURCES:
            raise ValueError(f"Unknown source: {source}")
        count = await self._news_repo.clear_content_by_source(source)
        async with self._state.news_lock:
            for item in self._state.news_store:
                if item.get("source") == source:
                    item["content"] = ""
        return {"source": source, "cleared": count}

    async def fetch_and_update_content(self, item: dict[str, Any]) -> dict[str, Any]:
        """Fetch full content for a news item and update caches."""
        news_id = item["news_id"]
        existing_content = item.get("content", "")
        summary = item.get("summary", "")
        if existing_content and existing_content != summary and not existing_content.startswith(summary[:50]):
            return {"news_id": news_id, "content": existing_content, "cached": True}

        url = item.get("url", "")
        if not url:
            return {"news_id": news_id, "content": summary, "cached": False, "source": "summary_only"}

        source = item.get("source", "")

        if source in deps.JS_RENDERED_SOURCES:
            content = await deps.fetch_article_content_via_jina(url)
            if content:
                item["content"] = content
                await self._news_repo.update_content(news_id, content)
                return {"news_id": news_id, "content": content, "cached": False, "source": "jina"}
            content = await deps.fetch_article_content(url)
            if content:
                item["content"] = content
                await self._news_repo.update_content(news_id, content)
                return {"news_id": news_id, "content": content, "cached": False, "source": "original"}
            return {"news_id": news_id, "content": summary, "cached": False, "source": "summary_only"}

        content = await deps.fetch_article_content(url)
        if not content:
            content = await deps.fetch_article_content_via_jina(url)
        if not content:
            return {"news_id": news_id, "content": summary, "cached": False, "source": "summary_only"}

        item["content"] = content
        await self._news_repo.update_content(news_id, content)
        return {"news_id": news_id, "content": content, "cached": False, "source": "original"}

    async def _bg_crawl_and_save(self, source: str, crawler) -> None:
        """Background task: crawl a single source and merge results."""
        try:
            items = await asyncio.wait_for(crawler.crawl(), timeout=15.0)
        except TimeoutError:
            logger.warning("[refresh] %s: crawl timed out after 15s", source)
            return
        except Exception as e:
            logger.warning("[refresh] %s crawl error: %s", source, e)
            return
        async with self._state.news_lock:
            filtered = self._keyword_filter.filter_newsitems(items)
            new_count = 0
            new_items = []
            for item in filtered:
                item_dict = item.to_dict()
                existing = any(n["news_id"] == item_dict["news_id"] for n in self._state.news_store)
                if not existing:
                    self._state.news_store.append(item_dict)
                    new_items.append(item_dict)
                    new_count += 1
            if new_items:
                await self._news_repo.upsert(new_items)
        logger.info("[refresh] %s done: %d total, %d new", source, len(items), new_count)
