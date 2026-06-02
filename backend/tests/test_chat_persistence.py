"""
聊天持久化集成测试
验证 chat 流程中消息自动保存到 SQLite
"""

import pytest
import tempfile
import os
import sqlite3

# 确保模型在 setup_db 之前被导入
from app.models.database import ChatSession, ChatMessage


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前确保表已创建，测试后清理数据"""
    from app.database import Base, engine
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_chat_saves_messages_to_db():
    """测试 chat 调用后消息自动保存到数据库"""
    from app.agent import chat
    from app.services.chat_log import ChatLogService
    from langgraph.checkpoint.sqlite import SqliteSaver

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "checkpoint.db")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            saver = SqliteSaver(conn)
            result = chat(
                message="你好",
                thread_id="persist-test-001",
                vector_store_service=None,
                checkpointer=saver,
            )
            assert "response" in result
            assert result["thread_id"] == "persist-test-001"

            # 验证消息已保存到数据库
            svc = ChatLogService()
            history = svc.get_history("persist-test-001")
            assert len(history) >= 2  # 至少有人类和 AI 两条消息

            roles = [m.role for m in history]
            assert "human" in roles
            assert "ai" in roles

            contents = [m.content for m in history]
            assert any("你好" in c for c in contents)
        finally:
            conn.close()


def test_chat_creates_session_if_not_exists():
    """测试 chat 调用时自动创建会话"""
    from app.agent import chat
    from app.services.chat_log import ChatLogService
    from langgraph.checkpoint.sqlite import SqliteSaver

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "checkpoint.db")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            saver = SqliteSaver(conn)
            result = chat(
                message="新会话消息",
                thread_id="new-sess-001",
                vector_store_service=None,
                checkpointer=saver,
            )
            assert "response" in result

            # 验证会话已创建
            svc = ChatLogService()
            session = svc.get_session("new-sess-001")
            assert session is not None
            assert session.session_id == "new-sess-001"
        finally:
            conn.close()
