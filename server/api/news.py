"""News-related API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from api import deps
from di.dependencies import get_news_service
from services.news import NewsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["news"])


@router.post("/news/refresh")
async def refresh_news(news_service: NewsService = Depends(get_news_service)):
    return await news_service.refresh_all()


@router.get("/news")
async def get_news(
    source: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    news_service: NewsService = Depends(get_news_service),
):
    return news_service.list_news(source, offset, limit)


@router.get("/news/{news_id}/content")
async def get_news_content(news_id: str, news_service: NewsService = Depends(get_news_service)):
    item = news_service.find_news(news_id)
    if not item:
        raise HTTPException(404, f"News not found: {news_id}")
    return await news_service.fetch_and_update_content(item)


@router.post("/news/refresh/{source}")
async def refresh_news_source(source: str, news_service: NewsService = Depends(get_news_service)):
    try:
        return await news_service.refresh_source(source)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/news/clear-cache/{source}")
async def clear_news_content_cache(source: str, news_service: NewsService = Depends(get_news_service)):
    try:
        return await news_service.clear_content_cache(source)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/sources")
async def get_sources():
    return {"sources": deps.NEWS_SOURCES}


@router.get("/newsnow/platforms")
async def get_newsnow_platforms():
    return {"platforms": {pid: deps.PLATFORM_CONFIG[pid]["name"] for pid in deps.NEWSNOW_CRAWLERS}}


@router.post("/newsnow/refresh")
async def refresh_newsnow(news_service: NewsService = Depends(get_news_service)):
    return await news_service.refresh_newsnow()


@router.post("/newsnow/refresh/{platform_id}")
async def refresh_newsnow_platform(platform_id: str, news_service: NewsService = Depends(get_news_service)):
    try:
        return await news_service.refresh_newsnow_platform(platform_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/rss/feeds")
async def get_rss_feeds():
    return {
        "feeds": [
            {"id": feed.id, "name": feed.name, "url": feed.url, "enabled": feed.enabled}
            for feed in deps.DEFAULT_RSS_FEEDS
        ]
    }


@router.post("/rss/refresh")
async def refresh_rss(news_service: NewsService = Depends(get_news_service)):
    return await news_service.refresh_rss()
