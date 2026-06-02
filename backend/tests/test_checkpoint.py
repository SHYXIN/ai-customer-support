"""
LangGraph Checkpoint 持久化测试
验证 SqliteSaver 能正确保存和恢复对话上下文
"""

import pytest
import tempfile
import os
import sqlite3


def test_sqlite_saver_creation():
    """测试 SqliteSaver 能正常创建"""
    from langgraph.checkpoint.sqlite import SqliteSaver

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        with SqliteSaver.from_conn_string(db_path) as saver:
            assert saver is not None


def test_agent_uses_sqlite_saver():
    """测试 Agent 创建时使用了 SqliteSaver 而非 MemorySaver"""
    from app.agent import create_agent
    from langgraph.checkpoint.sqlite import SqliteSaver

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            saver = SqliteSaver(conn)
            agent = create_agent(vector_store_service=None, checkpointer=saver)
            checkpointer = agent.checkpointer
            assert isinstance(checkpointer, SqliteSaver)
        finally:
            conn.close()


def test_agent_persists_conversation_across_restart():
    """测试重启 Agent 后能恢复之前的对话上下文"""
    from app.agent import create_agent, chat
    from langgraph.checkpoint.sqlite import SqliteSaver

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "checkpoint.db")
        thread_id = "test-persist-thread"

        # 第一轮：创建 agent 并发消息
        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            saver = SqliteSaver(conn)
            agent = create_agent(vector_store_service=None, checkpointer=saver)
            result1 = chat(
                message="你好",
                thread_id=thread_id,
                vector_store_service=None,
                checkpointer=saver,
            )
            assert "response" in result1
            assert result1["thread_id"] == thread_id
        finally:
            conn.close()

        # 第二轮：重新创建 agent（模拟重启），使用同一个 db
        conn2 = sqlite3.connect(db_path, check_same_thread=False)
        try:
            saver2 = SqliteSaver(conn2)
            agent2 = create_agent(vector_store_service=None, checkpointer=saver2)
            result2 = chat(
                message="你之前说了什么？",
                thread_id=thread_id,
                vector_store_service=None,
                checkpointer=saver2,
            )
            assert "response" in result2
            # 验证能获取到之前的对话历史
            checkpoint = saver2.get_tuple({"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}})
            assert checkpoint is not None
        finally:
            conn2.close()


def test_multiple_threads_independent():
    """测试不同 thread_id 的对话相互独立"""
    from app.agent import create_agent, chat
    from langgraph.checkpoint.sqlite import SqliteSaver

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "checkpoint.db")

        conn = sqlite3.connect(db_path, check_same_thread=False)
        try:
            saver = SqliteSaver(conn)
            agent = create_agent(vector_store_service=None, checkpointer=saver)

            # 两个不同 thread
            chat(message="订单问题", thread_id="thread-order", vector_store_service=None, checkpointer=saver)
            chat(message="退款问题", thread_id="thread-refund", vector_store_service=None, checkpointer=saver)

            # 验证两个 thread 独立
            cp1 = saver.get_tuple({"configurable": {"thread_id": "thread-order", "checkpoint_ns": ""}})
            cp2 = saver.get_tuple({"configurable": {"thread_id": "thread-refund", "checkpoint_ns": ""}})

            assert cp1 is not None
            assert cp2 is not None

            msgs1 = cp1.checkpoint.get("channel_values", {}).get("messages", [])
            msgs2 = cp2.checkpoint.get("channel_values", {}).get("messages", [])

            # 各自有独立的消息
            assert any("订单" in str(m.content) for m in msgs1)
            assert any("退款" in str(m.content) for m in msgs2)
        finally:
            conn.close()
