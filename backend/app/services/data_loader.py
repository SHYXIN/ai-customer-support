"""
Bitext 数据导入服务
负责读取 Bitext JSON 文件，清洗数据，并向量化存入 Chroma
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document

from app.config import settings
from app.services.embedding import BGEEmbeddingService
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class BitextDataLoader:
    """Bitext 数据加载器"""

    # Bitext 数据文件列表
    DATA_FILES = [
        "account.json",
        "all_categories.json",
        "contact.json",
        "delivery.json",
        "feedback.json",
        "invoice.json",
        "order.json",
        "payment.json",
        "refund.json",
        "shipping.json",
        "subscription.json",
    ]

    def __init__(
        self,
        data_dir: str = settings.bitext_data_dir,
    ):
        self.data_dir = Path(data_dir)

    def load_all_files(self) -> List[Dict[str, Any]]:
        """
        加载所有 Bitext JSON 文件

        Returns:
            合并后的数据条目列表
        """
        all_entries = []
        for filename in self.DATA_FILES:
            filepath = self.data_dir / filename
            if not filepath.exists():
                logger.warning(f"文件不存在，跳过: {filepath}")
                continue

            entries = self._load_single_file(filepath)
            logger.info(f"加载 {filename}: {len(entries)} 条记录")
            all_entries.extend(entries)

        logger.info(f"总共加载 {len(all_entries)} 条记录")
        return all_entries

    def _load_single_file(self, filepath: Path) -> List[Dict[str, Any]]:
        """加载单个 JSON 文件"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                logger.warning(f"文件 {filepath.name} 不是列表格式，跳过")
                return []
            return data
        except json.JSONDecodeError as e:
            logger.error(f"解析 {filepath.name} 失败: {e}")
            return []

    def clean_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        清洗单条数据

        过滤规则：
        - 必须有 instruction_cn 和 response_cn
        - instruction_cn 长度 > 2
        - response_cn 长度 > 5
        """
        instruction = entry.get("instruction_cn", "").strip()
        response = entry.get("response_cn", "").strip()

        if not instruction or len(instruction) <= 2:
            return None
        if not response or len(response) <= 5:
            return None

        return {
            "category": entry.get("category", "unknown"),
            "intent": entry.get("intent", "unknown"),
            "instruction": instruction,
            "response": response,
        }

    def deduplicate(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于 instruction 文本去重"""
        seen = set()
        unique_entries = []

        for entry in entries:
            key = entry["instruction"]
            if key not in seen:
                seen.add(key)
                unique_entries.append(entry)

        removed = len(entries) - len(unique_entries)
        if removed > 0:
            logger.info(f"去重: 移除 {removed} 条重复记录")

        return unique_entries

    def import_to_vector_store(
        self,
        embedding_service: BGEEmbeddingService,
        vector_store: VectorStoreService,
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        完整导入流程：加载 → 清洗 → 去重 → 向量化 → 存入 Chroma

        Args:
            embedding_service: BGE 嵌入服务
            vector_store: Chroma 向量存储服务
            batch_size: 批量向量化大小

        Returns:
            导入统计信息
        """
        # 1. 加载所有文件
        raw_entries = self.load_all_files()
        stats = {"total_raw": len(raw_entries)}

        # 2. 清洗
        cleaned = []
        for entry in raw_entries:
            cleaned_entry = self.clean_entry(entry)
            if cleaned_entry:
                cleaned.append(cleaned_entry)
        stats["after_clean"] = len(cleaned)

        # 3. 去重
        unique = self.deduplicate(cleaned)
        stats["after_dedup"] = len(unique)

        # 4. 分批向量化并导入
        total_imported = 0
        for i in range(0, len(unique), batch_size):
            batch = unique[i : i + batch_size]
            documents = []
            ids = []

            for j, entry in enumerate(batch):
                idx = i + j
                doc_id = hashlib.md5(entry["instruction"].encode()).hexdigest()[:16]
                doc = Document(
                    page_content=entry["instruction"],
                    metadata={
                        "category": entry["category"],
                        "intent": entry["intent"],
                        "response": entry["response"],
                    },
                )
                documents.append(doc)
                ids.append(f"bitext_{doc_id}")

            vector_store.add_documents(documents, ids=ids)
            total_imported += len(documents)
            logger.info(f"已导入 {total_imported}/{len(unique)} 条")

        stats["imported"] = total_imported
        logger.info(f"导入完成: {stats}")
        return stats

    def get_statistics(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取数据统计信息"""
        categories: Dict[str, int] = {}
        intents: Dict[str, int] = {}

        for entry in entries:
            cat = entry.get("category", "unknown")
            intent = entry.get("intent", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
            intents[intent] = intents.get(intent, 0) + 1

        return {
            "total": len(entries),
            "categories": dict(
                sorted(categories.items(), key=lambda x: x[1], reverse=True)
            ),
            "intents": dict(
                sorted(intents.items(), key=lambda x: x[1], reverse=True)[:20]
            ),
        }
