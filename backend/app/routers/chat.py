"""
对话接口
提供智能客服对话能力，接入 LangGraph Agent
自动保存聊天记录到 SQLite
"""

import logging
import uuid

from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.agent import chat as agent_chat

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    与智能体对话

    支持多轮对话，通过 session_id 关联上下文
    聊天记录自动持久化到 SQLite
    """
    # 延迟导入，避免循环导入
    from app.main import vector_store_service, checkpoint_saver

    session_id = request.session_id or str(uuid.uuid4())[:8]

    logger.info(f"对话请求 [{session_id}]: {request.message[:50]}...")

    try:
        result = agent_chat(
            message=request.message,
            thread_id=session_id,
            vector_store_service=vector_store_service,
            checkpointer=checkpoint_saver,
        )

        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            category=result.get("category", "general"),
            references=result.get("references", []),
        )
    except Exception as e:
        logger.error(f"对话失败: {e}")
        return ChatResponse(
            response="抱歉，服务暂时不可用，请稍后重试。",
            session_id=session_id,
            category="error",
        )
