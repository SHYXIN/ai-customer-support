"""
Pydantic 数据模型
定义 API 请求和响应的数据结构
"""

from typing import Optional
from pydantic import BaseModel, Field


# ============================================================
# 对话相关
# ============================================================


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, description="会话 ID（为空则创建新会话）")


class Reference(BaseModel):
    """引用来源"""
    content: str = Field(..., description="原始问题")
    response: str = Field(..., description="原始回答")
    category: str = Field("unknown", description="分类")
    score: float = Field(0.0, description="相似度分数")


class ChatResponse(BaseModel):
    """对话响应"""
    response: str = Field(..., description="AI 回答")
    session_id: str = Field(..., description="会话 ID")
    category: str = Field(..., description="问题分类")
    references: list[Reference] = Field(default_factory=list, description="引用来源")


class MessageHistory(BaseModel):
    """消息历史"""
    role: str = Field(..., description="角色：human / ai")
    content: str = Field(..., description="消息内容")


class HistoryResponse(BaseModel):
    """历史记录响应"""
    session_id: str = Field(..., description="会话 ID")
    messages: list[MessageHistory] = Field(default_factory=list, description="消息列表")


# ============================================================
# 知识库管理相关
# ============================================================


class ImportRequest(BaseModel):
    """数据导入请求"""
    data_dir: Optional[str] = Field(None, description="数据目录（为空则使用默认）")


class ImportResponse(BaseModel):
    """数据导入响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="提示信息")
    stats: dict = Field(default_factory=dict, description="导入统计")


class KnowledgeItem(BaseModel):
    """知识库条目"""
    content: str = Field(..., description="问题内容")
    metadata: dict = Field(default_factory=dict, description="元数据（分类、意图等）")


class KnowledgeListResponse(BaseModel):
    """知识库列表响应"""
    items: list[KnowledgeItem] = Field(default_factory=list, description="条目列表")
    total: int = Field(0, description="总数")
    limit: int = Field(20, description="每页数量")
    offset: int = Field(0, description="偏移量")


class SearchRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., description="查询文本")
    k: int = Field(5, description="返回数量")
    filter_dict: Optional[dict] = Field(None, description="过滤条件")


class SearchResponse(BaseModel):
    """检索响应"""
    query: str = Field(..., description="查询文本")
    results: list[KnowledgeItem] = Field(default_factory=list, description="结果列表")
    total: int = Field(0, description="结果总数")


# ============================================================
# 系统相关
# ============================================================


class StatsResponse(BaseModel):
    """统计信息响应"""
    total_documents: int = Field(0, description="知识库文档总数")
    collection_name: str = Field("", description="集合名称")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    embedding_loaded: bool = Field(False, description="嵌入模型是否加载")
    vector_store_loaded: bool = Field(False, description="向量数据库是否加载")
    document_count: int = Field(0, description="文档数量")
