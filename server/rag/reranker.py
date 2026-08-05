"""DashScope rerank (gte-rerank-v2) — 对 RRF 融合后的候选 chunk 精排。

调用 DashScope 文本重排接口，按 query 与每个文档的相关性打分，返回按分数
降序的 (原始索引, relevance_score) 列表。与 embedding/生图共用同一个
DASHSCOPE_API_KEY。走 raw HTTP（httpx async）而非 dashscope SDK，因为当前
锁定的 dashscope==1.14.0 不含 TextReRank。
"""

from __future__ import annotations

import logging

import httpx

from config import DASHSCOPE_API_KEY, KB_RERANK_MODEL

logger = logging.getLogger(__name__)

RERANK_URL = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"


class DashScopeReranker:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.model = model or KB_RERANK_MODEL

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_n: int | None = None,
    ) -> list[tuple[int, float]]:
        """按 query 相关性精排 documents。

        返回 (原始索引, relevance_score) 列表，按 relevance_score 降序；
        index 对应入参 documents 列表的下标。空 documents 返回 []，不调用 API。
        """
        if not documents:
            return []

        parameters: dict = {"return_documents": False}
        if top_n:
            parameters["top_n"] = top_n

        body = {
            "model": self.model,
            "input": {"query": query, "documents": documents},
            "parameters": parameters,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                RERANK_URL,
                json=body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            data = resp.json()

        # DashScope 错误响应含 code 字段（非 0/非空表示失败）
        if data.get("code"):
            raise RuntimeError(f"DashScope rerank failed: {data.get('code')} - {data.get('message')}")

        results = data.get("output", {}).get("results", [])
        return [(r["index"], r["relevance_score"]) for r in results]
