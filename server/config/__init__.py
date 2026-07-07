"""Configuration package for shiyuan-ai server.

Provides a pydantic-settings based ``Settings`` class for dependency injection
and re-exports legacy module-level constants for backward compatibility.
"""

from __future__ import annotations

from .dependencies import get_settings
from .settings import Settings

_settings = Settings()

# LLM
LLM_PROVIDER = _settings.llm_provider
LLM_API_KEY = _settings.llm_api_key
LLM_BASE_URL = _settings.llm_base_url
LLM_MODEL = _settings.llm_model

# Server
HOST = _settings.host
PORT = _settings.port

# Crawler
CRAWL_INTERVAL = _settings.crawl_interval
SCHEDULE_ENABLED = _settings.schedule_enabled
NEWSNOW_CRAWL_INTERVAL = _settings.newsnow_crawl_interval
RSS_CRAWL_INTERVAL = _settings.rss_crawl_interval
SCHEDULE_MIN_INTERVAL = _settings.schedule_min_interval

# Keywords
KEYWORDS_FILE = _settings.keywords_file
KEYWORDS_FILTER_ENABLED = _settings.keywords_filter_enabled

# Publishing
PUBLISH_RETRY = _settings.publish_retry
PUBLISH_HEADLESS = _settings.publish_headless
PUBLISH_TIMEOUT = _settings.publish_timeout
PUBLISH_MANUAL_TIMEOUT = _settings.publish_manual_timeout
COOKIES_DIR = _settings.cookies_dir

# Sources / NewsNow
NEWS_SOURCES = _settings.news_sources
NEWSNOW_PLATFORMS = _settings.newsnow_platforms
NEWSNOW_API_URL = _settings.newsnow_api_url
JINA_READER_URL = _settings.jina_reader_url

# Publish platforms
PUBLISH_PLATFORMS = _settings.publish_platforms

# WeChat
WECHAT_APP_ID = _settings.wechat_app_id
WECHAT_APP_SECRET = _settings.wechat_app_secret

# DashScope
DASHSCOPE_API_KEY = _settings.dashscope_api_key

# Image
IMAGE_GEN_ENABLED = _settings.image_gen_enabled
IMAGE_GEN_MODEL = _settings.image_gen_model

# CORS
CORS_ORIGINS = _settings.cors_origins

# Knowledge base
KB_CHUNK_SIZE = _settings.kb_chunk_size
KB_CHUNK_OVERLAP = _settings.kb_chunk_overlap
UPLOAD_DIR = _settings.upload_dir
MAX_UPLOAD_SIZE = _settings.max_upload_size
KB_EMBEDDING_DIM = _settings.kb_embedding_dim
KB_EMBEDDING_MODEL = _settings.kb_embedding_model
KB_VISION_MODEL = _settings.kb_vision_model
KB_VISION_BASE_URL = _settings.kb_vision_base_url

# Web search
WEB_SEARCH_ENABLED = _settings.web_search_enabled
WEB_SEARCH_ENGINE = _settings.web_search_engine
MOONSHOT_API_KEY = _settings.moonshot_api_key
TAVILY_API_KEY = _settings.tavily_api_key

# LangSmith
LANGSMITH_TRACING = _settings.langsmith_tracing
LANGSMITH_API_KEY = _settings.langsmith_api_key
LANGSMITH_PROJECT = _settings.langsmith_project
LANGSMITH_ENDPOINT = _settings.langsmith_endpoint

# Business DB
NEWS_AI_DB_PATH = _settings.news_ai_db_path

# Memory
MEMORY_DB_PATH = _settings.memory_db_path
SUMMARY_MODEL = _settings.summary_model
SUMMARY_MODEL_BASE_URL = _settings.summary_model_base_url
SUMMARY_MODEL_API_KEY = _settings.summary_model_api_key
SUMMARY_TRIGGER_TOKENS = _settings.summary_trigger_tokens
SUMMARY_KEEP_MESSAGES = _settings.summary_keep_messages

# KB RAG memory
KB_RAG_SUMMARY_TRIGGER_TOKENS = _settings.kb_rag_summary_trigger_tokens
KB_RAG_SUMMARY_KEEP_MESSAGES = _settings.kb_rag_summary_keep_messages
KB_RAG_MEMORY_DB_PATH = _settings.kb_rag_memory_db_path

# Temperatures
TEMPERATURE_REWRITE = _settings.temperature_rewrite
TEMPERATURE_SUMMARY = _settings.temperature_summary
TEMPERATURE_ANALYZE = _settings.temperature_analyze
TEMPERATURE_GENERATE = _settings.temperature_generate
TEMPERATURE_CHAT = _settings.temperature_chat

MAX_PROMPT_CHARS = _settings.max_prompt_chars
MAX_RAG_CONTEXT_CHARS = _settings.max_rag_context_chars

__all__ = [
    "Settings",
    "get_settings",
    "LLM_PROVIDER",
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "HOST",
    "PORT",
    "CRAWL_INTERVAL",
    "SCHEDULE_ENABLED",
    "NEWSNOW_CRAWL_INTERVAL",
    "RSS_CRAWL_INTERVAL",
    "SCHEDULE_MIN_INTERVAL",
    "KEYWORDS_FILE",
    "KEYWORDS_FILTER_ENABLED",
    "PUBLISH_RETRY",
    "PUBLISH_HEADLESS",
    "PUBLISH_TIMEOUT",
    "PUBLISH_MANUAL_TIMEOUT",
    "COOKIES_DIR",
    "NEWS_SOURCES",
    "NEWSNOW_PLATFORMS",
    "NEWSNOW_API_URL",
    "JINA_READER_URL",
    "PUBLISH_PLATFORMS",
    "WECHAT_APP_ID",
    "WECHAT_APP_SECRET",
    "DASHSCOPE_API_KEY",
    "IMAGE_GEN_ENABLED",
    "IMAGE_GEN_MODEL",
    "CORS_ORIGINS",
    "KB_CHUNK_SIZE",
    "KB_CHUNK_OVERLAP",
    "UPLOAD_DIR",
    "MAX_UPLOAD_SIZE",
    "KB_EMBEDDING_DIM",
    "KB_EMBEDDING_MODEL",
    "KB_VISION_MODEL",
    "KB_VISION_BASE_URL",
    "WEB_SEARCH_ENABLED",
    "WEB_SEARCH_ENGINE",
    "MOONSHOT_API_KEY",
    "TAVILY_API_KEY",
    "LANGSMITH_TRACING",
    "LANGSMITH_API_KEY",
    "LANGSMITH_PROJECT",
    "LANGSMITH_ENDPOINT",
    "MEMORY_DB_PATH",
    "SUMMARY_MODEL",
    "SUMMARY_MODEL_BASE_URL",
    "SUMMARY_MODEL_API_KEY",
    "SUMMARY_TRIGGER_TOKENS",
    "SUMMARY_KEEP_MESSAGES",
    "KB_RAG_SUMMARY_TRIGGER_TOKENS",
    "KB_RAG_SUMMARY_KEEP_MESSAGES",
    "KB_RAG_MEMORY_DB_PATH",
    "NEWS_AI_DB_PATH",
    "TEMPERATURE_REWRITE",
    "TEMPERATURE_SUMMARY",
    "TEMPERATURE_ANALYZE",
    "TEMPERATURE_GENERATE",
    "TEMPERATURE_CHAT",
    "MAX_PROMPT_CHARS",
    "MAX_RAG_CONTEXT_CHARS",
]
