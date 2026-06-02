"""
Chroma 向量数据库服务
管理文档的存储、检索、更新和删除
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


def _import_chroma():
    """导入 Chroma，优先使用新版 langchain-chroma"""
    try:
        from langchain_chroma import Chroma
        return Chroma
    except ImportError:
        from langchain_community.vectorstores import Chroma
        return Chroma


class VectorStoreService:
    """Chroma 向量数据库服务"""

    def __init__(
        self,
        persist_dir: str,
        embeddings: Embeddings,
        collection_name: str = "customer_service",
    ):
        """
        初始化向量数据库服务

        Args:
            persist_dir: Chroma 持久化目录
            embeddings: LangChain Embeddings 接口实例
            collection_name: 集合名称
        """
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self._embeddings = embeddings
        self._store: Optional[Any] = None

        # 确保持久化目录存在
        self.persist_dir.mkdir(parents=True, exist_ok=True)

    def initialize(self):
        """初始化或加载 Chroma 数据库"""
        Chroma = _import_chroma()
        logger.info(f"初始化 Chroma 数据库: {self.persist_dir}")
        self._store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self._embeddings,
            persist_directory=str(self.persist_dir),
        )
        logger.info(f"Chroma 数据库初始化完成，当前文档数: {self.count}")

    def add_documents(
        self,
        documents: List[Document],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """添加文档到向量数据库"""
        if not self._store:
            raise RuntimeError("数据库未初始化，请先调用 initialize()")

        added_ids = self._store.add_documents(documents, ids=ids)
        # 新版 langchain-chroma 自动持久化，无需手动调用 persist()
        if hasattr(self._store, "persist"):
            self._store.persist()
        logger.info(f"添加了 {len(added_ids)} 个文档")
        return added_ids

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """语义检索"""
        if not self._store:
            raise RuntimeError("数据库未初始化")

        return self._store.similarity_search(query, k=k, filter=filter_dict)

    def search_with_score(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[tuple]:
        """语义检索（带相似度分数）"""
        if not self._store:
            raise RuntimeError("数据库未初始化")

        return self._store.similarity_search_with_score(
            query, k=k, filter=filter_dict
        )

    def delete(self, ids: List[str]) -> bool:
        """删除文档"""
        if not self._store:
            raise RuntimeError("数据库未初始化")

        self._store.delete(ids=ids)
        logger.info(f"删除了 {len(ids)} 个文档")
        return True

    def get_by_metadata(self, filter_dict: Dict[str, Any]) -> List[Document]:
        """根据元数据过滤获取文档"""
        if not self._store:
            raise RuntimeError("数据库未初始化")

        return self._store.get(where=filter_dict)

    @property
    def count(self) -> int:
        """返回当前文档数量"""
        if not self._store:
            return 0
        return self._store._collection.count()
