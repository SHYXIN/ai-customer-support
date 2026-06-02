"""
聊天记录服务
负责将对话消息写入 SQLAlchemy 数据库，支持查询和删除
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.database import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class ChatLogService:
    """聊天记录服务，管理 chat_sessions 和 chat_messages 表"""

    def __init__(self, db: Session | None = None):
        """
        Args:
            db: SQLAlchemy Session 实例。为 None 时自动创建（调用方需管理生命周期）
        """
        self._db = db
        self._owns_session = db is None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def close(self):
        """关闭服务自己创建的 Session"""
        if self._owns_session and self._db is not None:
            self._db.close()
            self._db = None

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        title: Optional[str] = None,
    ) -> ChatMessage:
        """
        保存一条消息到数据库

        Args:
            session_id: 会话 ID
            role: 角色（"human" / "ai"）
            content: 消息内容
            title: 会话标题（仅在创建新会话时使用）

        Returns:
            创建的 ChatMessage 实例
        """
        now = datetime.now(timezone.utc)

        # 查找或创建 ChatSession
        stmt = select(ChatSession).where(ChatSession.session_id == session_id)
        cs = self.db.execute(stmt).scalars().first()

        if cs is None:
            cs = ChatSession(
                session_id=session_id,
                title=title or "新会话",
                created_at=now,
                updated_at=now,
            )
            self.db.add(cs)
            self.db.flush()  # 获取 cs.id
            logger.info(f"创建新会话: {session_id}")
        else:
            cs.updated_at = now
            if title:
                cs.title = title

        # 创建消息
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            created_at=now,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)

        logger.info(f"保存消息 [{session_id}] role={role} len={len(content)}")
        return msg

    def get_history(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatMessage]:
        """
        获取会话的消息历史

        Args:
            session_id: 会话 ID
            limit: 返回消息数量上限
            offset: 偏移量（用于分页）

        Returns:
            按时间升序排列的消息列表
        """
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_session(self, session_id: str) -> ChatSession | None:
        """获取会话信息"""
        stmt = select(ChatSession).where(ChatSession.session_id == session_id)
        return self.db.execute(stmt).scalars().first()

    def list_sessions(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ChatSession]:
        """列出所有会话（按更新时间降序）"""
        stmt = (
            select(ChatSession)
            .order_by(desc(ChatSession.updated_at))
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话及其所有消息（级联删除）

        Returns:
            是否成功删除
        """
        cs = self.get_session(session_id)
        if cs is None:
            return False
        self.db.delete(cs)
        self.db.commit()
        logger.info(f"删除会话: {session_id}")
        return True

    def rename_session(self, session_id: str, title: str) -> bool:
        """
        重命名会话

        Returns:
            是否成功重命名
        """
        cs = self.get_session(session_id)
        if cs is None:
            return False
        cs.title = title
        cs.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        logger.info(f"重命名会话: {session_id} → {title}")
        return True

    def get_message_count(self, session_id: str) -> int:
        """获取会话的消息数量"""
        from sqlalchemy import func
        stmt = (
            select(func.count(ChatMessage.id))
            .where(ChatMessage.session_id == session_id)
        )
        return self.db.execute(stmt).scalar() or 0
