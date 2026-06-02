"""
FastAPI 接口 TDD 测试
测试对话、搜索、管理接口
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

# 将 backend/ 根目录加入 Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mock_services():
    """模拟所有外部服务（使用 lifespan mock 避免加载真实模型）"""
    async def mock_lifespan(app):
        yield

    mock_store = MagicMock()
    mock_store.count = 956
    mock_store.collection_name = "customer_service"

    with patch("app.main.lifespan", mock_lifespan), \
         patch("app.main.vector_store_service", mock_store):
        yield


@pytest.fixture
def client(mock_services):
    """创建测试客户端"""
    from app.main import app
    return TestClient(app)


class TestHealthEndpoint:
    """健康检查接口测试"""

    def test_root_returns_service_info(self, client):
        """测试：根路径返回服务信息"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "service" in data

    def test_health_returns_healthy(self, client):
        """测试：健康检查返回 healthy"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestChatEndpoint:
    """对话接口测试"""

    def test_chat_returns_answer(self, client):
        """测试：对话接口返回回答"""
        with patch("app.agent.chat") as mock_agent_chat:
            mock_agent_chat.return_value = {
                "response": "这是一个测试回答",
                "thread_id": "default",
                "category": "order",
                "references": [],
            }
            response = client.post(
                "/api/chat",
                json={"message": "如何取消订单？"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "session_id" in data

    def test_chat_with_session_id(self, client):
        """测试：带 session_id 的对话"""
        with patch("app.agent.chat") as mock_agent_chat:
            mock_agent_chat.return_value = {
                "response": "回答",
                "thread_id": "test-session-123",
                "category": "general",
                "references": [],
            }
            response = client.post(
                "/api/chat",
                json={
                    "message": "我的订单状态是什么？",
                    "session_id": "test-session-123",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test-session-123"

    def test_chat_empty_message_returns_422(self, client):
        """测试：空消息返回 422 错误"""
        response = client.post(
            "/api/chat",
            json={"message": ""},
        )
        assert response.status_code == 422


class TestAdminEndpoints:
    """管理接口测试"""

    def test_stats_returns_document_count(self, client):
        """测试：统计接口返回文档数量"""
        response = client.get("/api/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
