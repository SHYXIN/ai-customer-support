"""
全局依赖模块
存放全局服务实例，避免循环导入
"""

from app.config import settings
from app.services.embedding import BGEEmbeddingService
from app.services.vector_store import VectorStoreService
from langchain_core.embeddings import Embeddings


class _EmbeddingsWrapper(Embeddings):
    """将 BGE 嵌入服务包装为 LangChain Embeddings 接口"""

    def __init__(self, embedding_service: BGEEmbeddingService):
        self._service = embedding_service

    def embed_documents(self, texts):
        return self._service.encode(texts)

    def embed_query(self, text):
        return self._service.encode_single(text)


# 全局服务实例（在 main.py 的 lifespan 中初始化）
embedding_service: BGEEmbeddingService | None = None
vector_store_service: VectorStoreService | None = None


def set_services(emb_svc: BGEEmbeddingService, store_svc: VectorStoreService) -> None:
    """设置全局服务实例（在 lifespan 中调用）"""
    global embedding_service, vector_store_service
    embedding_service = emb_svc
    vector_store_service = store_svc


def get_vector_store_service() -> VectorStoreService | None:
    """获取全局向量存储服务实例"""
    return vector_store_service


def get_embedding_service() -> BGEEmbeddingService | None:
    """获取全局嵌入服务实例"""
    return embedding_service
