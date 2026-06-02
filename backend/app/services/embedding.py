"""
BGE 嵌入服务
使用 ONNX Runtime 加载本地 BGE 模型，提供文本向量化能力
"""

import os
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class BGEEmbeddingService:
    """BGE 嵌入服务，基于 ONNX Runtime 推理"""

    def __init__(self, model_path: str):
        """
        初始化 BGE 嵌入服务

        Args:
            model_path: BGE 模型目录路径（包含 model_optimized.onnx 和 tokenizer.json）
                        支持相对路径（相对于当前工作目录）和绝对路径
        """
        # 如果是相对路径，相对于 backend/ 目录解析
        p = Path(model_path)
        if not p.is_absolute():
            backend_dir = Path(__file__).resolve().parent.parent.parent
            p = backend_dir / p
        self.model_path = p.resolve()
        self.model_file = self.model_path / "model_optimized.onnx"
        self.tokenizer_file = self.model_path / "tokenizer.json"

        self._session = None
        self._tokenizer = None

        self._validate_model()
        self._load_model()

    def _validate_model(self):
        """验证模型文件是否存在"""
        if not self.model_file.exists():
            raise FileNotFoundError(f"ONNX 模型文件不存在: {self.model_file}")
        if not self.tokenizer_file.exists():
            raise FileNotFoundError(f"分词器文件不存在: {self.tokenizer_file}")
        logger.info(f"BGE 模型路径: {self.model_path}")

    def _load_model(self):
        """加载 ONNX 模型和分词器"""
        try:
            from optimum.onnxruntime import ORTModelForFeatureExtraction
            from transformers import AutoTokenizer

            logger.info("正在加载 BGE ONNX 模型...")
            self._session = ORTModelForFeatureExtraction.from_pretrained(
                str(self.model_path),
                file_name="model_optimized.onnx",
                provider="CPUExecutionProvider",
            )
            self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            logger.info("BGE 模型加载完成")
        except ImportError:
            logger.warning(
                "optimum 未安装，使用备用方案（需要安装 optimum[onnxruntime]）"
            )
            self._load_model_fallback()

    def _load_model_fallback(self):
        """备用加载方案：使用 onnxruntime + transformers"""
        import onnxruntime as ort
        from transformers import AutoTokenizer

        logger.info("使用备用方案加载 ONNX 模型...")
        self._session = ort.InferenceSession(str(self.model_file))
        self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        logger.info("BGE 模型加载完成（备用方案）")

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        将文本列表转换为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表，每个向量是 float 列表
        """
        if not self._session or not self._tokenizer:
            raise RuntimeError("模型未加载")

        # 分词
        inputs = self._tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np",
        )

        # ONNX 推理
        if hasattr(self._session, "forward"):
            # optimum 方案
            import torch
            inputs_torch = {k: torch.tensor(v) for k, v in inputs.items()}
            outputs = self._session.forward(**inputs_torch)
            embeddings = outputs.last_hidden_state.detach().numpy()
        else:
            # 纯 onnxruntime 方案
            ort_inputs = {k: v for k, v in inputs.items()}
            outputs = self._session.run(None, ort_inputs)
            embeddings = outputs[0]

        # 取 [CLS] 向量作为句子嵌入
        cls_embeddings = embeddings[:, 0, :]

        # L2 归一化
        norms = np.linalg.norm(cls_embeddings, axis=1, keepdims=True)
        cls_embeddings = cls_embeddings / (norms + 1e-8)

        return cls_embeddings.tolist()

    def encode_single(self, text: str) -> List[float]:
        """将单条文本转换为向量"""
        return self.encode([text])[0]

    @property
    def dimension(self) -> int:
        """返回向量维度"""
        return 512
