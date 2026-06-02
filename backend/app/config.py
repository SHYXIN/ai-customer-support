"""应用配置"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录（config.py 在 backend/app/ 下）
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM 配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.longcat.chat/openai"
    openai_model: str = "LongCat-2.0-Preview"

    # BGE 嵌入模型配置（相对于 backend/ 目录）
    bge_model_path: str = "bge-small-zh-v1.5/fast-bge-small-zh-v1.5"
    embedding_dimension: int = 512

    # Chroma 向量数据库配置
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "customer_service"

    # Bitext 数据配置（相对于 backend/ 目录）
    bitext_data_dir: str = "bitext_cn"

    # 检索配置
    retrieval_top_k: int = 3

    # SQLite 数据库配置
    db_path: str = "./data/app.db"

    def resolve_path(self, path: str) -> Path:
        """将相对于 backend/ 的路径转为绝对路径"""
        p = Path(path)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        return p.resolve()


settings = Settings()
