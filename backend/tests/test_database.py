"""
数据库基础设施测试
验证 SQLAlchemy 引擎、Session 和模型定义
"""

import pytest
from sqlalchemy import text

# 确保模型在 init_db 之前被导入，注册到 Base.metadata
from app.models.database import ChatSession, ChatMessage


@pytest.fixture(autouse=True)
def setup_db():
    """每个测试前确保表已创建，测试后清理数据"""
    from app.database import init_db, SessionLocal
    init_db()
    yield
    # 清理测试数据
    session = SessionLocal()
    try:
        session.query(ChatMessage).delete()
        session.query(ChatSession).delete()
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def test_database_engine_creation():
    """测试数据库引擎能正常创建"""
    from app.database import engine

    assert engine is not None
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_session_factory_creation():
    """测试 SessionLocal 工厂能创建会话"""
    from app.database import SessionLocal

    session = SessionLocal()
    assert session is not None
    session.close()


def test_session_commit_and_rollback():
    """测试会话能正常提交和回滚"""
    from app.database import SessionLocal

    session = SessionLocal()
    try:
        cs = ChatSession(session_id="test-001", title="测试会话")
        session.add(cs)
        session.commit()

        result = session.query(ChatSession).filter_by(session_id="test-001").first()
        assert result is not None
        assert result.title == "测试会话"
    finally:
        session.rollback()
        session.close()


def test_chat_session_model_columns():
    """测试 ChatSession 模型有正确的列"""
    columns = {c.name for c in ChatSession.__table__.columns}
    expected = {"id", "session_id", "title", "created_at", "updated_at"}
    assert expected.issubset(columns)


def test_chat_message_model_columns():
    """测试 ChatMessage 模型有正确的列"""
    columns = {c.name for c in ChatMessage.__table__.columns}
    expected = {"id", "session_id", "role", "content", "created_at"}
    assert expected.issubset(columns)


def test_base_metadata():
    """测试 Base 元数据中有预期的表"""
    from app.database import Base

    table_names = set(Base.metadata.tables.keys())
    assert "chat_sessions" in table_names
    assert "chat_messages" in table_names
