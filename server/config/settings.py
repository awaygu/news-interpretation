"""Injectable settings using pydantic-settings.

This module provides a ``Settings`` class that reads configuration from
environment variables and ``.env`` files. The legacy ``config.py`` re-exports
old module-level constants for backward compatibility.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Values are read from environment variables (case-insensitive) and ``.env``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # LLM
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-v4-flash"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Crawler / schedule
    crawl_interval: int = 1800
    schedule_enabled: bool = True
    newsnow_crawl_interval: int = 1800
    rss_crawl_interval: int = 1800
    schedule_min_interval: int = 60

    # Keywords
    keywords_file: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "keywords.txt")
    keywords_filter_enabled: bool = True

    # Publishing
    publish_retry: int = 3
    publish_headless: bool = True
    publish_timeout: int = 60
    publish_manual_timeout: int = 600
    cookies_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "cookies")

    # External services
    newsnow_api_url: str = "https://newsnow.busiyi.world/api/s"
    jina_reader_url: str = "https://r.jina.ai"

    # WeChat
    wechat_app_id: str = ""
    wechat_app_secret: str = ""

    # DashScope
    dashscope_api_key: str = ""

    # Image generation
    image_gen_enabled: bool = True
    image_gen_model: str = "qwen-image-2.0-pro"

    # CORS
    cors_origins: str = "*"

    # Knowledge base
    kb_chunk_size: int = 500
    kb_chunk_overlap: int = 50
    upload_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "uploads")
    max_upload_size: int = 20 * 1024 * 1024
    kb_embedding_dim: int = 1024
    kb_embedding_model: str = "text-embedding-v4"
    kb_vision_model: str = "qwen-vl-ocr-latest"
    kb_vision_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Web search
    web_search_enabled: bool = False
    web_search_engine: str = "tavily"
    moonshot_api_key: str = ""
    tavily_api_key: str = ""

    # LangSmith
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "shiyuan-ai"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # Memory
    memory_db_path: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data" / "agent_memory.db")
    summary_model: str = "deepseek-v4-flash"
    summary_model_base_url: str = ""
    summary_model_api_key: str = ""
    summary_trigger_tokens: int = 80000
    summary_keep_messages: int = 10

    # Business DB
    news_ai_db_path: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "news_ai.db")
    # KB RAG memory
    kb_rag_summary_trigger_tokens: int = 50000
    kb_rag_summary_keep_messages: int = 8
    kb_rag_memory_db_path: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data" / "rag_memory.db")

    # Temperatures
    temperature_rewrite: float = 0.0
    temperature_summary: float = 0.3
    temperature_analyze: float = 0.7
    temperature_generate: float = 0.8
    temperature_chat: float = 0.7

    # Prompt guardrails
    max_rag_context_chars: int = 15000

    @model_validator(mode="after")
    def _set_summary_defaults(self) -> Settings:
        if not self.summary_model_base_url:
            self.summary_model_base_url = self.llm_base_url
        if not self.summary_model_api_key:
            self.summary_model_api_key = self.llm_api_key
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def news_sources(self) -> dict[str, str]:
        return {
            "cls-hot": "财联社热门",
            "cls-telegraph": "财联社电报",
            "wallstreetcn-hot": "华尔街见闻",
            "cankaoxiaoxi": "参考消息",
            "thepaper": "澎湃新闻",
            "toutiao": "今日头条",
            "xueqiu": "雪球",
            "weibo": "微博",
            "douyin": "抖音",
            "hacker-news": "Hacker News",
            "ruanyifeng": "阮一峰的网络日志",
        }

    @property
    def newsnow_platforms(self) -> dict[str, str]:
        return {
            "cls-hot": "财联社热门",
            "cls-telegraph": "财联社电报",
            "wallstreetcn-hot": "华尔街见闻",
            "cankaoxiaoxi": "参考消息",
            "thepaper": "澎湃新闻",
            "toutiao": "今日头条",
            "xueqiu": "雪球",
            "weibo": "微博",
            "douyin": "抖音",
        }

    @property
    def publish_platforms(self) -> dict[str, str]:
        return {
            "xiaohongshu": "小红书",
            "wechat_mp": "微信公众号",
            "douyin": "抖音",
        }

    @property
    def max_prompt_chars(self) -> dict[str, int]:
        return {
            "interpret": 4000,
            "chat": 2000,
            "generate": 4000,
            "agent": 4000,
            "kb_rag": 2000,
            "kb_generate": 2000,
        }
