"""
LangGraph Agent TDD 测试
测试 chat 函数返回引用数据
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# 将 backend/ 根目录加入 Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from langchain_core.messages import AIMessage


class TestAgentChat:
    """Agent chat 函数测试"""

    @pytest.fixture
    def mock_vector_store(self):
        """模拟向量存储"""
        store = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "如何取消订单"
        mock_doc.metadata = {
            "response": "您可以登录账户取消订单",
            "category": "ORDER",
        }
        store.search.return_value = [mock_doc]
        return store

    @pytest.fixture
    def mock_llm_response(self):
        """模拟 LLM 响应（使用真实 AIMessage）"""
        return AIMessage(content="根据知识库，您可以登录账户取消订单。")

    def test_chat_returns_response(self, mock_vector_store, mock_llm_response):
        """测试：chat 函数返回回答"""
        with patch("app.agent.create_llm") as mock_create_llm:
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm.invoke.return_value = mock_llm_response
            mock_create_llm.return_value = mock_llm

            # 每次调用都重新导入以清除缓存
            import importlib
            from app import agent
            importlib.reload(agent)

            result = agent.chat("怎么退货", thread_id="test-001", vector_store_service=mock_vector_store)

            assert "response" in result
            assert isinstance(result["response"], str)
            assert len(result["response"]) > 0

    def test_chat_returns_references(self, mock_vector_store, mock_llm_response):
        """测试：chat 函数返回引用数据"""
        with patch("app.agent.create_llm") as mock_create_llm:
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm.invoke.return_value = mock_llm_response
            mock_create_llm.return_value = mock_llm

            import importlib
            from app import agent
            importlib.reload(agent)

            result = agent.chat("怎么退货", thread_id="test-002", vector_store_service=mock_vector_store)

            assert "references" in result
            assert isinstance(result["references"], list)
            assert len(result["references"]) > 0

    def test_chat_reference_has_required_fields(self, mock_vector_store, mock_llm_response):
        """测试：引用包含必要字段"""
        with patch("app.agent.create_llm") as mock_create_llm:
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm.invoke.return_value = mock_llm_response
            mock_create_llm.return_value = mock_llm

            import importlib
            from app import agent
            importlib.reload(agent)

            result = agent.chat("怎么退货", thread_id="test-003", vector_store_service=mock_vector_store)

            ref = result["references"][0]
            assert "content" in ref
            assert "response" in ref
            assert "category" in ref

    def test_chat_returns_category(self, mock_vector_store, mock_llm_response):
        """测试：chat 函数返回分类"""
        with patch("app.agent.create_llm") as mock_create_llm:
            mock_llm = MagicMock()
            mock_llm.bind_tools.return_value = mock_llm
            mock_llm.invoke.return_value = mock_llm_response
            mock_create_llm.return_value = mock_llm

            import importlib
            from app import agent
            importlib.reload(agent)

            result = agent.chat("怎么退货", thread_id="test-004", vector_store_service=mock_vector_store)

            assert "category" in result
            assert isinstance(result["category"], str)
