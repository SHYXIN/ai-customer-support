"""
向量存储服务 TDD 测试
测试 Chroma 向量数据库的增删查功能
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path

# 确保 app 模块可导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


# ============================================================
# 红阶段：先写测试，运行失败
# ============================================================


class TestVectorStoreService:
    """向量存储服务测试"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        tmp = tempfile.mkdtemp()
        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    @pytest.fixture
    def mock_embedding(self):
        """模拟嵌入服务"""
        class MockEmbedding:
            def embed_documents(self, texts):
                # 返回简单的 one-hot 向量（仅用于测试）
                import random
                random.seed(42)
                return [[random.random() for _ in range(8)] for _ in texts]

            def embed_query(self, text):
                import random
                random.seed(42)
                return [random.random() for _ in range(8)]

        return MockEmbedding()

    @pytest.fixture
    def vector_store(self, temp_dir, mock_embedding):
        """创建向量存储实例"""
        from app.services.vector_store import VectorStoreService

        store = VectorStoreService(
            persist_dir=temp_dir,
            embeddings=mock_embedding,
            collection_name="test_collection",
        )
        store.initialize()
        return store

    def test_initialize_creates_collection(self, vector_store):
        """测试：初始化后集合被创建"""
        assert vector_store.count == 0

    def test_add_documents(self, vector_store):
        """测试：添加文档成功"""
        from langchain_core.documents import Document

        docs = [
            Document(page_content="如何取消订单", metadata={"category": "order"}),
            Document(page_content="如何退款", metadata={"category": "refund"}),
        ]
        ids = vector_store.add_documents(docs)

        assert len(ids) == 2
        assert vector_store.count == 2

    def test_search_returns_results(self, vector_store):
        """测试：语义检索返回结果"""
        from langchain_core.documents import Document

        docs = [
            Document(page_content="如何取消订单", metadata={"category": "order"}),
            Document(page_content="如何退款", metadata={"category": "refund"}),
            Document(page_content="如何查询物流", metadata={"category": "shipping"}),
        ]
        vector_store.add_documents(docs)

        results = vector_store.search("取消订单", k=2)

        assert len(results) > 0
        assert len(results) <= 2

    def test_search_with_score(self, vector_store):
        """测试：检索返回相似度分数"""
        from langchain_core.documents import Document

        docs = [
            Document(page_content="如何取消订单", metadata={"category": "order"}),
        ]
        vector_store.add_documents(docs)

        results = vector_store.search_with_score("取消订单", k=1)

        assert len(results) == 1
        doc, score = results[0]
        assert isinstance(score, float)

    def test_delete_documents(self, vector_store):
        """测试：删除文档"""
        from langchain_core.documents import Document

        docs = [
            Document(page_content="如何取消订单", metadata={"category": "order"}),
        ]
        ids = vector_store.add_documents(docs)
        assert vector_store.count == 1

        vector_store.delete(ids)
        assert vector_store.count == 0

    def test_get_by_metadata(self, vector_store):
        """测试：按元数据过滤"""
        from langchain_core.documents import Document

        docs = [
            Document(page_content="如何取消订单", metadata={"category": "order"}),
            Document(page_content="如何退款", metadata={"category": "refund"}),
        ]
        vector_store.add_documents(docs)

        results = vector_store.get_by_metadata({"category": "order"})
        assert len(results) >= 1
