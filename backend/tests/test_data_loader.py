"""
Bitext 数据加载器 TDD 测试
测试数据加载、清洗、去重功能
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# 确保 app 模块可导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app.services.data_loader import BitextDataLoader


class TestBitextDataLoader:
    """Bitext 数据加载器测试"""

    @pytest.fixture
    def sample_data_dir(self):
        """创建临时测试数据目录"""
        tmp = tempfile.mkdtemp()

        # 创建测试用的 JSON 文件
        order_data = [
            {
                "category": "ORDER",
                "intent": "cancel_order",
                "instruction_cn": "如何取消订单",
                "response_cn": "您可以登录账户，在订单详情页点击取消按钮。",
            },
            {
                "category": "ORDER",
                "intent": "cancel_order",
                "instruction_cn": "怎么取消订单",
                "response_cn": "您可以登录账户，在订单详情页点击取消按钮。",
            },
            {
                "category": "ORDER",
                "intent": "cancel_order",
                "instruction_cn": "如何取消订单",  # 重复
                "response_cn": "您可以登录账户，在订单详情页点击取消按钮。",
            },
        ]
        with open(os.path.join(tmp, "order.json"), "w", encoding="utf-8") as f:
            json.dump(order_data, f, ensure_ascii=False)

        refund_data = [
            {
                "category": "REFUND",
                "intent": "request_refund",
                "instruction_cn": "如何申请退款",
                "response_cn": "您可以在订单详情页申请退款，我们会在 3-5 个工作日内处理。",
            },
        ]
        with open(os.path.join(tmp, "refund.json"), "w", encoding="utf-8") as f:
            json.dump(refund_data, f, ensure_ascii=False)

        yield tmp

        # 清理
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    @pytest.fixture
    def loader(self, sample_data_dir):
        """创建数据加载器实例"""
        return BitextDataLoader(data_dir=sample_data_dir)

    def test_load_single_file(self, loader, sample_data_dir):
        """测试：加载单个 JSON 文件"""
        filepath = Path(sample_data_dir) / "order.json"
        entries = loader._load_single_file(filepath)

        assert len(entries) == 3
        assert entries[0]["category"] == "ORDER"
        assert entries[0]["intent"] == "cancel_order"

    def test_load_all_files(self, loader):
        """测试：加载所有 JSON 文件"""
        entries = loader.load_all_files()

        # order.json (3条) + refund.json (1条) = 4条
        assert len(entries) == 4

    def test_clean_entry_valid(self, loader):
        """测试：清洗有效数据"""
        entry = {
            "category": "ORDER",
            "intent": "cancel_order",
            "instruction_cn": "如何取消订单",
            "response_cn": "您可以登录账户取消订单。",
        }
        result = loader.clean_entry(entry)

        assert result is not None
        assert result["instruction"] == "如何取消订单"
        assert result["response"] == "您可以登录账户取消订单。"

    def test_clean_entry_missing_instruction(self, loader):
        """测试：缺少 instruction_cn 的数据被过滤"""
        entry = {
            "category": "ORDER",
            "intent": "cancel_order",
            "instruction_cn": "",
            "response_cn": "您可以登录账户取消订单。",
        }
        result = loader.clean_entry(entry)

        assert result is None

    def test_clean_entry_missing_response(self, loader):
        """测试：缺少 response_cn 的数据被过滤"""
        entry = {
            "category": "ORDER",
            "intent": "cancel_order",
            "instruction_cn": "如何取消订单",
            "response_cn": "",
        }
        result = loader.clean_entry(entry)

        assert result is None

    def test_clean_entry_too_short(self, loader):
        """测试：太短的内容被过滤"""
        entry = {
            "category": "ORDER",
            "intent": "cancel_order",
            "instruction_cn": "好",  # 太短
            "response_cn": "好",     # 太短
        }
        result = loader.clean_entry(entry)

        assert result is None

    def test_deduplicate(self, loader):
        """测试：基于 instruction 去重"""
        entries = [
            {"instruction": "如何取消订单", "response": "回答1", "category": "ORDER", "intent": "cancel"},
            {"instruction": "如何取消订单", "response": "回答2", "category": "ORDER", "intent": "cancel"},
            {"instruction": "如何退款", "response": "回答3", "category": "REFUND", "intent": "refund"},
        ]
        result = loader.deduplicate(entries)

        assert len(result) == 2
        assert result[0]["instruction"] == "如何取消订单"
        assert result[1]["instruction"] == "如何退款"

    def test_get_statistics(self, loader):
        """测试：数据统计"""
        entries = [
            {"category": "ORDER", "intent": "cancel_order", "instruction": "如何取消", "response": "回答1"},
            {"category": "ORDER", "intent": "place_order", "instruction": "如何下单", "response": "回答2"},
            {"category": "REFUND", "intent": "request_refund", "instruction": "如何退款", "response": "回答3"},
        ]
        stats = loader.get_statistics(entries)

        assert stats["total"] == 3
        assert stats["categories"]["ORDER"] == 2
        assert stats["categories"]["REFUND"] == 1
        assert "cancel_order" in stats["intents"]

    def test_full_pipeline(self, loader):
        """测试：完整流程（加载 -> 清洗 -> 去重）"""
        raw_entries = loader.load_all_files()
        assert len(raw_entries) == 4

        cleaned = []
        for entry in raw_entries:
            result = loader.clean_entry(entry)
            if result:
                cleaned.append(result)
        assert len(cleaned) == 4  # 4条都有效

        unique = loader.deduplicate(cleaned)
        assert len(unique) == 3  # 去重后剩3条（1条重复）

        stats = loader.get_statistics(unique)
        assert stats["total"] == 3
