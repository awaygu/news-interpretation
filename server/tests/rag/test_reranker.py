"""DashScopeReranker 测试：空文档短路、正常返回、错误响应、top_n 透传（mock httpx）。

不真实调用 DashScope，mock httpx.AsyncClient.post 返回构造的 rerank 响应。
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag import reranker as rer_mod
from rag.reranker import DashScopeReranker


class _FakeResponse:
    """模拟 httpx.Response，只暴露 json()。"""

    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def _patch_post(payload: dict, *, sink: dict[str, Any] | None = None):
    """patch httpx.AsyncClient.post，使其返回带 payload 的 _FakeResponse。

    sink 若提供，则记录最后一次调用的 json body，用于断言 top_n 等参数透传。
    返回 patch 上下文管理器。
    """
    async def _fake_post(self, url, json=None, headers=None, **kwargs):
        if sink is not None:
            sink["body"] = json
            sink["url"] = url
        return _FakeResponse(payload)

    return patch.object(rer_mod.httpx.AsyncClient, "post", _fake_post)


async def test_rerank_empty_documents_returns_empty():
    """空文档列表直接返回 []，不发起 HTTP 调用。"""
    rr = DashScopeReranker(api_key="dummy")
    with patch.object(rer_mod.httpx.AsyncClient, "post", AsyncMock()) as mock_post:
        result = await rr.rerank("q", [], top_n=3)
    assert result == []
    mock_post.assert_not_called()


async def test_rerank_returns_index_score_pairs_sorted():
    """正常响应返回 (index, relevance_score) 列表，按服务端返回顺序（降序）。"""
    payload = {
        "output": {
            "results": [
                {"index": 0, "relevance_score": 0.95},
                {"index": 2, "relevance_score": 0.41},
                {"index": 1, "relevance_score": 0.12},
            ]
        },
        "usage": {"total_tokens": 123},
        "request_id": "req-1",
    }
    rr = DashScopeReranker(api_key="dummy")
    with _patch_post(payload):
        result = await rr.rerank("LangGraph 是什么", ["a", "b", "c"], top_n=3)
    assert result == [(0, 0.95), (2, 0.41), (1, 0.12)]


async def test_rerank_top_n_passed_in_parameters():
    """top_n 透传到请求体 parameters，return_documents 固定 False。"""
    sink: dict[str, Any] = {}
    payload = {"output": {"results": [{"index": 0, "relevance_score": 0.9}]}}
    rr = DashScopeReranker(api_key="dummy", model="gte-rerank-v2")
    with _patch_post(payload, sink=sink):
        await rr.rerank("q", ["a"], top_n=5)
    assert sink["body"]["parameters"] == {"return_documents": False, "top_n": 5}
    assert sink["body"]["model"] == "gte-rerank-v2"
    assert sink["body"]["input"]["query"] == "q"
    assert sink["body"]["input"]["documents"] == ["a"]


async def test_rerank_without_top_n_omits_parameter():
    """未传 top_n 时 parameters 只含 return_documents。"""
    sink: dict[str, Any] = {}
    payload = {"output": {"results": [{"index": 0, "relevance_score": 0.9}]}}
    rr = DashScopeReranker(api_key="dummy")
    with _patch_post(payload, sink=sink):
        await rr.rerank("q", ["a"])
    assert sink["body"]["parameters"] == {"return_documents": False}


async def test_rerank_error_code_raises_runtime_error():
    """响应含 code 字段（非空）时抛 RuntimeError。"""
    payload = {"code": "InvalidApiKey", "message": "API key invalid", "request_id": "x"}
    rr = DashScopeReranker(api_key="dummy")
    with _patch_post(payload):
        with pytest.raises(RuntimeError, match="DashScope rerank failed"):
            await rr.rerank("q", ["a"], top_n=1)


async def test_rerank_uses_config_defaults_when_unset():
    """不传 api_key/model 时回退到 config 默认值（DASHSCOPE_API_KEY / KB_RERANK_MODEL）。"""
    sink: dict[str, Any] = {}
    payload = {"output": {"results": [{"index": 0, "relevance_score": 0.9}]}}
    rr = DashScopeReranker()
    # conftest 注入 DASHSCOPE_API_KEY=dummy、config 默认 KB_RERANK_MODEL=gte-rerank-v2
    assert rr.api_key == "dummy"
    assert rr.model == "gte-rerank-v2"
    with _patch_post(payload, sink=sink):
        await rr.rerank("q", ["a"])
    assert sink["body"]["model"] == "gte-rerank-v2"


async def test_rerank_missing_results_key_returns_empty():
    """output.results 缺失时返回 []（不抛错，交给上层回退处理）。"""
    payload = {"output": {}, "usage": {"total_tokens": 0}}
    rr = DashScopeReranker(api_key="dummy")
    with _patch_post(payload):
        result = await rr.rerank("q", ["a"])
    assert result == []
