"""
聊天记录服务测试
验证消息自动保存到 SQLite
"""

import pytest
from app.database import Base, engine


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前确保表已创建，测试后清理"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_save_message():
    """测试保存消息到数据库"""
    from app.services.chat_log import ChatLogService

    svc = ChatLogService()
    msg = svc.save_message(session_id="test-001", role="human", content="你好", title="测试")

    assert msg.id is not None
    assert msg.session_id == "test-001"
    assert msg.role == "human"
    assert msg.content == "你好"


def test_get_history():
    """测试获取聊天记录"""
    from app.services.chat_log import ChatLogService

    svc = ChatLogService()
    svc.save_message(session_id="test-002", role="human", content="你好", title="测试")
    svc.save_message(session_id="test-002", role="ai", content="您好")

    history = svc.get_history("test-002")
    assert len(history) == 2
    assert history[0].role == "human"
    assert history[0].content == "你好"
    assert history[1].role == "ai"
    assert history[1].content == "您好"


def test_get_history_empty():
    """测试获取不存在的会话记录"""
    from app.services.chat_log import ChatLogService

    svc = ChatLogService()
    history = svc.get_history("nonexistent")
    assert len(history) == 0


def test_list_sessions():
    """测试列出所有会话"""
    from app.services.chat_log import ChatLogService

    svc = ChatLogService()
    svc.save_message(session_id="sess-001", role="human", content="A", title="会话A")
    svc.save_message(session_id="sess-002", role="human", content="B", title="会话B")

    sessions = svc.list_sessions()
    assert len(sessions) == 2


def test_delete_session_cascades():
    """测试删除会话级联删除消息"""
    from app.services.chat_log import ChatLogService

    svc = ChatLogService()
    svc.save_message(session_id="del-001", role="human", content="消息1", title="删除测试")
    svc.save_message(session_id="del-001", role="ai", content="回复1")

    svc.delete_session("del-001")

    history = svc.get_history("del-001")
    assert len(history) == 0
