"""
BGE 嵌入服务 TDD 测试
测试 ONNX 本地推理能力
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


class TestBGEEmbeddingService:
    """BGE 嵌入服务测试"""

    @pytest.fixture(scope="class")
    def embedding_service(self):
        """创建 BGE 服务实例（整个测试类共享）"""
        from app.services.embedding import BGEEmbeddingService
        # 使用 config 中的路径（相对于 backend/ 目录）
        from app.config import settings
        model_path = settings.bge_model_path
        return BGEEmbeddingService(model_path)

    def test_model_loads_successfully(self, embedding_service):
        """测试：模型加载成功"""
        assert embedding_service._session is not None
        assert embedding_service._tokenizer is not None

    def test_encode_single_text(self, embedding_service):
        """测试：单条文本向量化"""
        vector = embedding_service.encode_single("这是一个测试")

        assert isinstance(vector, list)
        assert len(vector) == 512
        assert all(isinstance(v, float) for v in vector)

    def test_encode_multiple_texts(self, embedding_service):
        """测试：批量文本向量化"""
        texts = ["如何取消订单", "如何退款", "如何查询物流"]
        vectors = embedding_service.encode(texts)

        assert len(vectors) == 3
        assert all(len(v) == 512 for v in vectors)

    def test_vectors_are_normalized(self, embedding_service):
        """测试：向量已 L2 归一化（模长 ≈ 1）"""
        import math

        vector = embedding_service.encode_single("测试文本")
        magnitude = math.sqrt(sum(v**2 for v in vector))

        assert abs(magnitude - 1.0) < 0.01

    def test_similar_texts_have_high_similarity(self, embedding_service):
        """测试：相似文本的余弦相似度高"""
        import math

        v1 = embedding_service.encode_single("如何取消订单")
        v2 = embedding_service.encode_single("怎么取消订单")
        v3 = embedding_service.encode_single("今天天气怎么样")

        def cosine_similarity(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            return dot  # 已归一化，直接点积即可

        sim_similar = cosine_similarity(v1, v2)
        sim_different = cosine_similarity(v1, v3)

        assert sim_similar > sim_different
        assert sim_similar > 0.8

    def test_dimension_property(self, embedding_service):
        """测试：dimension 属性返回正确值"""
        assert embedding_service.dimension == 512
