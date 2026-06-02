"""
LangGraph 客服智能体
基于 ReAct 模式：检索知识库 → 生成回答 → 可选工具调用
"""

import logging
from typing import Annotated, TypedDict, Optional, Literal

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from app.tools.customer_service import (
    query_order_status,
    query_logistics,
    query_return_policy,
    query_payment_methods,
    query_shipping_fee,
)

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """智能体状态"""
    messages: Annotated[list, add_messages]  # 对话历史
    context: str  # 检索到的知识库上下文
    category: str  # 当前问题分类
    tool_calls: list  # 工具调用记录
    references: list  # 检索到的引用文档


# 系统提示词
SYSTEM_PROMPT = """你是一个专业的客服助手。请根据以下原则回答用户问题：

1. 优先使用提供的知识库上下文回答
2. 如果需要查询订单、物流等信息，使用相应工具
3. 回答要简洁、专业、有礼貌
4. 如果不确定，如实告知用户

知识库上下文：{context}
"""


def create_llm():
    """创建 LLM 实例"""
    from app.config import settings

    kwargs = {
        "model": settings.openai_model,
        "temperature": 0.7,
        "api_key": settings.openai_api_key,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


def create_agent(vector_store_service=None, checkpointer=None):
    """
    创建客服智能体

    Args:
        vector_store_service: 向量数据库服务实例（可选）
        checkpointer: LangGraph checkpointer 实例（可选，默认 MemorySaver）

    Returns:
        编译后的 LangGraph 应用
    """
    llm = create_llm()
    tools = [query_order_status, query_logistics, query_return_policy]
    llm_with_tools = llm.bind_tools(tools)

    def retrieve_node(state: AgentState) -> dict:
        """检索节点：从知识库获取相关上下文"""
        last_msg = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_msg = msg
                break

        if not last_msg:
            return {"context": "", "category": "unknown", "references": []}

        query = last_msg.content

        references = []
        context_parts = []
        if vector_store_service:
            results = vector_store_service.search(query, k=3)
            for doc in results:
                response = doc.metadata.get("response", "")
                category = doc.metadata.get("category", "general")
                if response:
                    context_parts.append(f"Q: {doc.page_content}\nA: {response}")
                    references.append({
                        "content": doc.page_content,
                        "response": response,
                        "category": category,
                    })

        context = "\n\n".join(context_parts) if context_parts else "暂无相关知识库内容。"

        # 简单分类
        category = "general"
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["订单", "order", "购买"]):
            category = "order"
        elif any(kw in query_lower for kw in ["物流", "快递", "配送", "shipping"]):
            category = "logistics"
        elif any(kw in query_lower for kw in ["退款", "退货", "refund", "return"]):
            category = "refund"

        return {"context": context, "category": category, "references": references}

    def generate_node(state: AgentState) -> dict:
        """生成节点：调用 LLM 生成回答"""
        context = state.get("context", "")

        system_content = SYSTEM_PROMPT.format(context=context)
        system_msg = SystemMessage(content=system_content)

        messages = [system_msg] + state["messages"]

        response = llm_with_tools.invoke(messages)

        return {"messages": [response]}

    # 构建图
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)

    # 添加边
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    # 使用传入的 checkpointer，默认 MemorySaver
    if checkpointer is None:
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()

    # 编译图
    app = graph.compile(checkpointer=checkpointer)

    return app


def chat(
    message: str,
    thread_id: str = "default",
    vector_store_service=None,
    checkpointer=None,
) -> dict:
    """
    与智能体对话

    Args:
        message: 用户消息
        thread_id: 会话 ID（用于多轮对话）
        vector_store_service: 向量数据库服务
        checkpointer: LangGraph checkpointer 实例

    Returns:
        包含回答和元信息的字典
    """
    # 每次调用都创建新 agent，避免全局单例导致 checkpointer 被复用
    agent = create_agent(vector_store_service, checkpointer)

    config = {"configurable": {"thread_id": thread_id}}

    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config,
    )

    # 提取最后一条 AI 回复
    ai_response = None
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            ai_response = msg
            break

    # 构建引用列表
    references = []
    for ref in result.get("references", []):
        references.append({
            "content": ref.get("content", ""),
            "response": ref.get("response", ""),
            "category": ref.get("category", ""),
        })

    ai_content = ai_response.content if ai_response else "抱歉，我无法回答这个问题。"

    # 保存聊天记录到 SQLite（幂等：路由层也会保存，但 save_message 使用 INSERT OR IGNORE）
    try:
        from app.services.chat_log import ChatLogService
        chat_log = ChatLogService()
        chat_log.save_message(thread_id, "human", message)
        chat_log.save_message(thread_id, "ai", ai_content)
        chat_log.close()
    except Exception as e:
        logger.warning(f"保存聊天记录失败: {e}")

    return {
        "response": ai_content,
        "thread_id": thread_id,
        "category": result.get("category", "unknown"),
        "references": references,
    }
