"""
聊天记录 API
提供会话列表、消息历史、删除会话等接口
"""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import HistoryResponse, MessageHistory

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat-history"])


@router.get("/sessions")
async def list_sessions(
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """
    列出所有会话（按更新时间降序）
    """
    from app.services.chat_log import ChatLogService

    svc = ChatLogService()
    try:
        sessions = svc.list_sessions(limit=limit, offset=offset)
        return {
            "sessions": [
                {
                    "session_id": s.session_id,
                    "title": s.title,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                    "message_count": svc.get_message_count(s.session_id),
                }
                for s in sessions
            ],
            "total": len(sessions),
        }
    finally:
        svc.close()


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=200, description="返回消息数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """
    获取指定会话的消息历史
    """
    from app.services.chat_log import ChatLogService

    svc = ChatLogService()
    try:
        messages = svc.get_history(session_id, limit=limit, offset=offset)
        return HistoryResponse(
            session_id=session_id,
            messages=[
                MessageHistory(
                    role=msg.role,
                    content=msg.content,
                )
                for msg in messages
            ],
        )
    finally:
        svc.close()


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    删除指定会话及其所有消息
    """
    from app.services.chat_log import ChatLogService

    svc = ChatLogService()
    try:
        deleted = svc.delete_session(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        return {"success": True, "message": f"会话 {session_id} 已删除"}
    finally:
        svc.close()


@router.put("/sessions/{session_id}/rename")
async def rename_session(session_id: str, body: dict):
    """
    重命名会话
    """
    from app.services.chat_log import ChatLogService

    title = body.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")

    svc = ChatLogService()
    try:
        session = svc.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        svc.rename_session(session_id, title)
        return {"success": True, "message": f"会话已重命名为: {title}"}
    finally:
        svc.close()
