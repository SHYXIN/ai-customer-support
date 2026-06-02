"""
服务模块
提供全局服务实例，避免循环导入
"""

from app.services.embedding import BGEEmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.data_loader import BitextDataLoader

__all__ = ["BGEEmbeddingService", "VectorStoreService", "BitextDataLoader"]
