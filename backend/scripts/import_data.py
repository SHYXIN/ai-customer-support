"""
Bitext 数据导入脚本
将 Bitext 中文客服对话数据清洗、向量化后存入 Chroma
"""

import sys
from pathlib import Path

# 将 backend/ 根目录加入 Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.services.embedding import BGEEmbeddingService
from app.services.vector_store import VectorStoreService
from app.services.data_loader import BitextDataLoader


def main():
    print("=" * 60)
    print("Bitext 数据导入")
    print("=" * 60)

    # 1. 加载 BGE 嵌入模型
    print("\n[1/4] 加载 BGE 嵌入模型...")
    embedding_service = BGEEmbeddingService(settings.bge_model_path)
    print(f"  BGE 模型加载完成，向量维度: {embedding_service.dimension}")

    # 2. 初始化 Chroma 向量数据库
    print("\n[2/4] 初始化 Chroma 向量数据库...")
    # 将 BGE 嵌入服务包装为 LangChain Embeddings 接口
    from langchain_core.embeddings import Embeddings

    class _EmbeddingsWrapper(Embeddings):
        def embed_documents(self, texts):
            return embedding_service.encode(texts)
        def embed_query(self, text):
            return embedding_service.encode_single(text)

    vector_store = VectorStoreService(
        persist_dir=settings.chroma_persist_dir,
        embeddings=_EmbeddingsWrapper(),
    )
    vector_store.initialize()
    print(f"  Chroma 数据库初始化完成，当前文档数: {vector_store.count}")

    # 3. 加载并导入 Bitext 数据
    print("\n[3/4] 加载 Bitext 数据...")
    loader = BitextDataLoader(data_dir=settings.bitext_data_dir)
    stats = loader.import_to_vector_store(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    # 4. 显示结果
    print("\n[4/4] 导入结果:")
    print(f"  原始记录数: {stats['total_raw']}")
    print(f"  清洗后记录数: {stats['after_clean']}")
    print(f"  去重后记录数: {stats['after_dedup']}")
    print(f"  成功导入: {stats['imported']}")
    print(f"  当前数据库文档数: {vector_store.count}")

    print("\n" + "=" * 60)
    print("数据导入完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
