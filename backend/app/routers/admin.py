"""
管理接口
知识库管理、数据统计、系统配置
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    ImportRequest,
    ImportResponse,
    KnowledgeItem,
    KnowledgeListResponse,
    SearchRequest,
    SearchResponse,
    StatsResponse,
)
from app.services.data_loader import BitextDataLoader

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])

# 延迟导入，避免循环引用
_vector_store = None
_embedding_service = None


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        from app.main import vector_store_service as vector_store
        _vector_store = vector_store
    return _vector_store


def get_embedding_service():
    global _embedding_service
    if _embedding_service is None:
        from app.main import embedding_service
        _embedding_service = embedding_service
    return _embedding_service


@router.post("/import", response_model=ImportResponse)
async def import_data(request: ImportRequest):
    """导入 Bitext 数据到向量数据库"""
    try:
        loader = BitextDataLoader(data_dir=request.data_dir)
        stats = loader.import_to_vector_store(
            embedding_service=get_embedding_service(),
            vector_store=get_vector_store(),
        )
        return ImportResponse(
            success=True,
            message="数据导入完成",
            stats=stats,
        )
    except Exception as e:
        logger.error(f"导入失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """获取知识库统计信息"""
    try:
        store = get_vector_store()
        return StatsResponse(
            total_documents=store.count,
            collection_name=store.collection_name,
        )
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(request: SearchRequest):
    """语义检索知识库"""
    try:
        store = get_vector_store()
        results = store.search(
            query=request.query,
            k=request.k,
            filter_dict=request.filter_dict,
        )
        items = [
            KnowledgeItem(
                content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in results
        ]
        return SearchResponse(
            query=request.query,
            results=items,
            total=len(items),
        )
    except Exception as e:
        logger.error(f"检索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge", response_model=KnowledgeListResponse)
async def list_knowledge(
    category: Optional[str] = Query(None, description="按类别过滤"),
    limit: int = Query(20, description="返回数量"),
    offset: int = Query(0, description="偏移量"),
):
    """列出知识库条目"""
    try:
        store = get_vector_store()
        filter_dict = {"category": category} if category else None
        results = store.get_by_metadata(filter_dict) if filter_dict else []

        # 分页
        paginated = results[offset : offset + limit]

        items = [
            KnowledgeItem(
                content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in paginated
        ]
        return KnowledgeListResponse(
            items=items,
            total=len(results),
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"列出知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
