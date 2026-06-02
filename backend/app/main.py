"""
AI 客服系统 — FastAPI 主入口
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.embedding import BGEEmbeddingService
from app.services.vector_store import VectorStoreService
from app.database import init_db
from langchain_core.embeddings import Embeddings


class _EmbeddingsWrapper(Embeddings):
    """将 BGE 嵌入服务包装为 LangChain Embeddings 接口"""

    def __init__(self, embedding_service: BGEEmbeddingService):
        self._service = embedding_service

    def embed_documents(self, texts):
        return self._service.encode(texts)

    def embed_query(self, text):
        return self._service.encode_single(text)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 全局服务实例（在 lifespan 中初始化）
embedding_service: BGEEmbeddingService | None = None
vector_store_service: VectorStoreService | None = None
checkpoint_saver = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时加载模型，关闭时清理资源"""
    global embedding_service, vector_store_service, checkpoint_saver

    logger.info("=" * 60)
    logger.info("AI 客服系统启动中...")
    logger.info("=" * 60)

    # 1. 初始化数据库
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")

    # 2. 加载 BGE 嵌入模型
    logger.info("正在加载 BGE 嵌入模型...")
    embedding_service = BGEEmbeddingService(settings.bge_model_path)
    logger.info(f"BGE 模型加载完成，向量维度: {embedding_service.dimension}")

    # 3. 初始化 Chroma 向量数据库
    logger.info("正在初始化 Chroma 向量数据库...")
    vector_store_service = VectorStoreService(
        persist_dir=settings.chroma_persist_dir,
        embeddings=_EmbeddingsWrapper(embedding_service),
    )
    vector_store_service.initialize()
    logger.info(f"Chroma 数据库初始化完成，当前文档数: {vector_store_service.count}")

    # 4. 初始化 SqliteSaver（对话上下文持久化）
    logger.info("正在初始化 SqliteSaver...")
    import sqlite3
    from langgraph.checkpoint.sqlite import SqliteSaver
    # SqliteSaver 需要 sqlite3.Connection 实例，不是连接字符串
    checkpoint_conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    checkpoint_saver = SqliteSaver(checkpoint_conn)
    logger.info("SqliteSaver 初始化完成")

    logger.info("=" * 60)
    logger.info("AI 客服系统启动完成")
    logger.info("=" * 60)

    yield

    # 关闭时清理
    logger.info("AI 客服系统关闭中...")
    if checkpoint_saver is not None:
        checkpoint_saver.conn.close()
        logger.info("SqliteSaver 已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="AI Customer Service System",
    description="基于 LangGraph 的智能客服系统",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径 — 服务状态检查"""
    return {
        "status": "running",
        "service": "AI Customer Service System",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "embedding_loaded": embedding_service is not None,
        "vector_store_loaded": vector_store_service is not None,
        "document_count": vector_store_service.count if vector_store_service else 0,
    }


# 导入路由
from app.routers import chat, admin, history

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(history.router, prefix="/api/chat", tags=["chat-history"])
