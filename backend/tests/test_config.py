"""
配置模块测试
"""

from app.config import settings


def test_settings_has_required_fields():
    """测试配置包含所有必要字段"""
    assert hasattr(settings, "openai_api_key")
    assert hasattr(settings, "openai_base_url")
    assert hasattr(settings, "openai_model")
    assert hasattr(settings, "bge_model_path")
    assert hasattr(settings, "embedding_dimension")
    assert hasattr(settings, "chroma_persist_dir")
    assert hasattr(settings, "chroma_collection_name")
    assert hasattr(settings, "bitext_data_dir")
    assert hasattr(settings, "retrieval_top_k")


def test_settings_default_values():
    """测试配置默认值"""
    assert settings.openai_base_url == "https://api.longcat.chat/openai"
    assert settings.openai_model == "LongCat-2.0-Preview"
    assert settings.embedding_dimension == 512
    assert settings.chroma_collection_name == "customer_service"
    assert settings.retrieval_top_k == 3
