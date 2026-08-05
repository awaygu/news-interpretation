"""_rerank_or_fallback 测试：rerank 精排与回退 RRF 的行为。

直接测 rag_graph._rerank_or_fallback（retrieve 节点的精排/回退逻辑收拢处），
不跑完整 graph，避免 mock 一长串检索依赖。chunk_data 结构仿 database.load_kb_chunk_texts。
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import config as config_mod
import core.rag_graph as rag_mod


def _chunk_data(ids: list[str]) -> dict[str, dict]:
    """构造 load_kb_chunk_texts 风格的 chunk 字典。"""
    return {
        cid: {
            "chunk_id": cid,
            "text": f"text-{cid}",
            "page": 0,
            "doc_id": "doc1",
            "filename": f"{cid}.md",
        }
        for cid in ids
    }


async def test_rerank_success_reorders_by_relevance():
    """rerank 成功时按返回的 (index, score) 重排 chunk_id，顺序与 RRF 不同。"""
    ids = ["c0", "c1", "c2"]
    fused = [("c0", 0.03), ("c1", 0.02), ("c2", 0.01)]  # RRF 顺序 c0>c1>c2
    chunk_data = _chunk_data(ids)

    fake_rerank = AsyncMock(return_value=[(2, 0.95), (0, 0.41), (1, 0.12)])  # rerank 偏爱 c2

    with (
        patch.object(config_mod, "KB_RERANK_ENABLED", True),
        patch.object(config_mod, "DASHSCOPE_API_KEY", "dummy"),
    ):
        # _rerank_or_fallback 内部 import DashScopeReranker，patch 模块属性
        with patch("rag.reranker.DashScopeReranker") as RR:
            RR.return_value.rerank = fake_rerank
            result = await rag_mod._rerank_or_fallback(
                "q", ids, chunk_data, fused, max_chunks=5
            )

    # rerank 把 c2 提到第一
    assert [cid for cid, _ in result] == ["c2", "c0", "c1"]
    assert result[0][1] == 0.95  # rerank 分数


async def test_rerank_disabled_falls_back_to_rrf():
    """KB_RERANK_ENABLED=false 时回退 RRF 顺序，不调用 rerank。"""
    ids = ["c0", "c1", "c2"]
    fused = [("c0", 0.03), ("c1", 0.02), ("c2", 0.01)]
    chunk_data = _chunk_data(ids)

    with patch.object(config_mod, "KB_RERANK_ENABLED", False):
        with patch("rag.reranker.DashScopeReranker") as RR:
            result = await rag_mod._rerank_or_fallback("q", ids, chunk_data, fused, max_chunks=5)
            RR.assert_not_called()

    assert [cid for cid, _ in result] == ["c0", "c1", "c2"]  # RRF 顺序
    assert result[0][1] == 0.03  # rrf 分数


async def test_rerank_missing_api_key_falls_back_to_rrf():
    """DASHSCOPE_API_KEY 为空时回退 RRF，不调用 rerank。"""
    ids = ["c0", "c1"]
    fused = [("c0", 0.03), ("c1", 0.02)]
    chunk_data = _chunk_data(ids)

    with (
        patch.object(config_mod, "KB_RERANK_ENABLED", True),
        patch.object(config_mod, "DASHSCOPE_API_KEY", ""),
    ):
        with patch("rag.reranker.DashScopeReranker") as RR:
            result = await rag_mod._rerank_or_fallback("q", ids, chunk_data, fused, max_chunks=5)
            RR.assert_not_called()

    assert [cid for cid, _ in result] == ["c0", "c1"]


async def test_rerank_exception_falls_back_to_rrf():
    """rerank 抛异常时回退 RRF 顺序，不向上抛。"""
    ids = ["c0", "c1", "c2"]
    fused = [("c0", 0.03), ("c1", 0.02), ("c2", 0.01)]
    chunk_data = _chunk_data(ids)

    fake_rerank = AsyncMock(side_effect=RuntimeError("network timeout"))

    with (
        patch.object(config_mod, "KB_RERANK_ENABLED", True),
        patch.object(config_mod, "DASHSCOPE_API_KEY", "dummy"),
    ):
        with patch("rag.reranker.DashScopeReranker") as RR:
            RR.return_value.rerank = fake_rerank
            result = await rag_mod._rerank_or_fallback("q", ids, chunk_data, fused, max_chunks=5)

    assert [cid for cid, _ in result] == ["c0", "c1", "c2"]  # 回退 RRF 顺序
    assert result[0][1] == 0.03


async def test_rerank_empty_result_falls_back_to_rrf():
    """rerank 返回空列表时视为失败，回退 RRF。"""
    ids = ["c0", "c1"]
    fused = [("c0", 0.03), ("c1", 0.02)]
    chunk_data = _chunk_data(ids)

    fake_rerank = AsyncMock(return_value=[])

    with (
        patch.object(config_mod, "KB_RERANK_ENABLED", True),
        patch.object(config_mod, "DASHSCOPE_API_KEY", "dummy"),
    ):
        with patch("rag.reranker.DashScopeReranker") as RR:
            RR.return_value.rerank = fake_rerank
            result = await rag_mod._rerank_or_fallback("q", ids, chunk_data, fused, max_chunks=5)

    assert [cid for cid, _ in result] == ["c0", "c1"]


async def test_rrf_fallback_truncates_to_max_chunks():
    """回退路径截断到 max_chunks，不返回全部候选。"""
    ids = ["c0", "c1", "c2", "c3", "c4"]
    fused = [(cid, 0.05 - i * 0.01) for i, cid in enumerate(ids)]
    chunk_data = _chunk_data(ids)

    with patch.object(config_mod, "KB_RERANK_ENABLED", False):
        result = await rag_mod._rerank_or_fallback("q", ids, chunk_data, fused, max_chunks=2)

    assert len(result) == 2
    assert [cid for cid, _ in result] == ["c0", "c1"]


async def test_rerank_top_n_capped_to_max_chunks():
    """rerank 路径 top_n 透传 max_chunks，服务端只返回 ≤max_chunks 条。"""
    ids = ["c0", "c1", "c2", "c3"]
    fused = [("c0", 0.04), ("c1", 0.03), ("c2", 0.02), ("c3", 0.01)]
    chunk_data = _chunk_data(ids)

    # 服务端按 top_n=2 只返回 2 条
    fake_rerank = AsyncMock(return_value=[(2, 0.9), (0, 0.5)])

    with (
        patch.object(config_mod, "KB_RERANK_ENABLED", True),
        patch.object(config_mod, "DASHSCOPE_API_KEY", "dummy"),
    ):
        with patch("rag.reranker.DashScopeReranker") as RR:
            RR.return_value.rerank = fake_rerank
            result = await rag_mod._rerank_or_fallback("q", ids, chunk_data, fused, max_chunks=2)

    fake_rerank.assert_called_once_with("q", ["text-c0", "text-c1", "text-c2", "text-c3"], top_n=2)
    assert len(result) == 2
    assert [cid for cid, _ in result] == ["c2", "c0"]


async def test_empty_ids_returns_empty():
    """ids 为空时直接返回空列表。"""
    with patch.object(config_mod, "KB_RERANK_ENABLED", True):
        with patch("rag.reranker.DashScopeReranker") as RR:
            result = await rag_mod._rerank_or_fallback("q", [], {}, [], max_chunks=5)
            RR.assert_not_called()
    assert result == []
