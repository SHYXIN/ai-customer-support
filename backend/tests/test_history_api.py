"""
历史记录 API 测试
验证聊天记录查询和删除接口
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前确保表已创建，测试后清理数据"""
    from app.database import init_db, SessionLocal
    from app.models.database import ChatSession, ChatMessage
    init_db()
    yield
    session = SessionLocal()
    try:
        session.query(ChatMessage).delete()
        session.query(ChatSession).delete()
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def client():
    """创建测试客户端（不加载完整 lifespan）"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def seed_data():
    """预置测试数据"""
    from app.services.chat_log import ChatLogService

    svc = ChatLogService()
    svc.save_message(session_id="api-sess-001", role="human", content="你好", title="API测试会话")
    svc.save_message(session_id="api-sess-001", role="ai", content="您好，有什么可以帮您？")
    svc.save_message(session_id="api-sess-002", role="human", content="订单问题", title="订单会话")
    svc.close()


def test_list_sessions_endpoint(client, seed_data):
    """测试 GET /api/chat/sessions 返回会话列表"""
    response = client.get("/api/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert len(data["sessions"]) == 2


def test_get_session_history_endpoint(client, seed_data):
    """测试 GET /api/chat/history/{session_id} 返回消息历史"""
    response = client.get("/api/chat/history/api-sess-001")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "api-sess-001"
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "human"
    assert data["messages"][0]["content"] == "你好"
    assert data["messages"][1]["role"] == "ai"


def test_get_history_empty_session(client, seed_data):
    """测试获取不存在会话的历史"""
    response = client.get("/api/chat/history/nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["messages"] == []


def test_delete_session_endpoint(client, seed_data):
    """测试 DELETE /api/chat/sessions/{session_id} 删除会话"""
    response = client.delete("/api/chat/sessions/api-sess-001")
    assert response.status_code == 200

    # 验证已删除
    response2 = client.get("/api/chat/history/api-sess-001")
    data2 = response2.json()
    assert data2["messages"] == []


def test_health_check_includes_db(client):
    """测试健康检查接口"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_rename_session_endpoint(client, seed_data):
    """测试 PUT /api/chat/sessions/{session_id}/rename 重命名会话"""
    response = client.put(
        "/api/chat/sessions/api-sess-001/rename",
        json={"title": "新标题"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # 验证标题已更新
    response2 = client.get("/api/chat/sessions")
    data2 = response2.json()
    session = next(s for s in data2["sessions"] if s["session_id"] == "api-sess-001")
    assert session["title"] == "新标题"


def test_rename_session_not_found(client, seed_data):
    """测试重命名不存在的会话返回 404"""
    response = client.put(
        "/api/chat/sessions/nonexistent/rename",
        json={"title": "新标题"},
    )
    assert response.status_code == 404
