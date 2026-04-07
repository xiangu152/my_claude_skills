#!/usr/bin/env python3
"""
嵌入模型统一接口
支持两种实现框架：
  - requests: 联网 API（NVIDIA NIM 等）
  - transformers: 本地模型（torch + transformers，支持 MPS GPU 加速）

使用方式：
  # 联网模式（requests）
  model = get_embedding_model(provider="nvidia", api_key="xxx", model="nvidia/nv-embed-v1")

  # 本地模式（transformers）
  model = get_embedding_model(provider="transformers", model_path="/path/to/model")
"""

import os
from abc import ABC, abstractmethod
from typing import Optional

import requests
import torch


class EmbeddingModel(ABC):
    """嵌入模型基类"""

    # 子类应设置的维度
    DIM: int = 4096
    MODEL_NAME: str = "unknown"

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...

    @property
    def provider(self) -> str:
        """返回 provider 名称"""
        return self.__class__.__name__.replace("Embeddings", "").lower()


# ─────────────────────────────────────────
# NVIDIA NIM（requests 联网）
# ─────────────────────────────────────────
class NvidiaEmbeddings(EmbeddingModel):
    """
    使用 NVIDIA NIM API 进行向量化
    接入点: https://integrate.api.nvidia.com/v1/embeddings

    支持的嵌入模型：
      - nvidia/nv-embed-v1        （4096 维，通用型，推荐）
      - nvidia/llama-nemotron-embed-1b-v2
      - baai/bge-m3
    """

    DIM = 4096
    MODEL_NAME = "nvidia/nv-embed-v1"
    MAX_BATCH_SIZE = 50

    def __init__(
        self,
        model: str = "nvidia/nv-embed-v1",
        api_key: Optional[str] = None,
        base_url: str = "https://integrate.api.nvidia.com/v1/embeddings",
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "未设置 NVIDIA API Key。\n"
                "请到 https://build.nvidia.com 免费注册获取 API Key，\n"
                "方式1: 设置环境变量 export NVIDIA_API_KEY=your_key\n"
                "方式2: 初始化时传入 api_key 参数"
            )
        self.base_url = base_url
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, payload: dict) -> dict:
        resp = requests.post(
            self.base_url,
            json=payload,
            headers=self._headers,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    def embed_query(self, text: str) -> list[float]:
        result = self._post({"input": text, "model": self.model})
        return result["data"][0]["embedding"]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """分批调用 API，避免单次请求过大"""
        all_embeddings = []
        for i in range(0, len(texts), self.MAX_BATCH_SIZE):
            batch = texts[i : i + self.MAX_BATCH_SIZE]
            result = self._post({"input": batch, "model": self.model})
            embeddings = [None] * len(batch)
            for item in result["data"]:
                embeddings[item["index"]] = item["embedding"]
            all_embeddings.extend(embeddings)
        return all_embeddings


# ─────────────────────────────────────────
# Transformers 本地模型（torch + transformers）
# ─────────────────────────────────────────
class TransformersEmbeddings(EmbeddingModel):
    """
    使用本地 transformers 模型进行向量化

    支持 Apple Silicon MPS GPU 加速，自动检测设备。

    环境变量：
      RAG_EMBED_MODEL_PATH: 模型路径（默认 ~/.cache/huggingface/...）
    """

    DIM = 1024  # 默认维度，可通过 init 覆盖

    def __init__(
        self,
        model_path: Optional[str] = None,
        dim: int = 1024,
        device: Optional[str] = None,
        max_length: int = 512,
    ):
        self.model_path = model_path or os.environ.get(
            "RAG_EMBED_MODEL_PATH",
            "/Users/xiangu/Codes/models/qwen3-0.6B-embedding",
        )
        self.dim = dim
        self.max_length = max_length

        # 设备选择：优先 MPS，其次 CUDA，最后 CPU
        if device:
            self.device = torch.device(device)
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """延迟加载模型（只加载一次）"""
        if self._model is None:
            from transformers import AutoTokenizer, AutoModel

            print(f"[TransformersEmbeddings] 加载模型: {self.model_path}", flush=True)
            print(f"[TransformersEmbeddings] 设备: {self.device}", flush=True)

            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_path, trust_remote_code=True
            )
            self._model = AutoModel.from_pretrained(
                self.model_path, trust_remote_code=True
            )
            self._model = self._model.to(self.device)
            self._model.eval()

            print(f"[TransformersEmbeddings] 模型加载完成，维度: {self.dim}", flush=True)

    def embed_query(self, text: str) -> list[float]:
        emb = self._embed_single(text)
        return emb

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_single(t) for t in texts]

    def _embed_single(self, text: str) -> list[float]:
        """对单条文本生成嵌入向量"""
        self._load_model()

        inputs = self._tokenizer(
            text[:3000],
            return_tensors="pt",
            truncation=True,
            max_length=self.max_length,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)
            # Mean pooling
            emb = outputs.last_hidden_state.mean(dim=1).squeeze().float().cpu().numpy()

        return emb.tolist()


# ─────────────────────────────────────────
# 工厂函数
# ─────────────────────────────────────────
def get_embedding_model(
    provider: str = "nvidia",
    api_key: Optional[str] = None,
    **kwargs,
) -> EmbeddingModel:
    """
    获取嵌入模型实例

    Args:
        provider: "nvidia" | "transformers"
        api_key: API Key（nvidia 需要）
        **kwargs: 传递给具体模型的参数

    Returns:
        EmbeddingModel 实例
    """
    if provider == "nvidia":
        return NvidiaEmbeddings(
            model=kwargs.get("model", "nvidia/nv-embed-v1"),
            api_key=api_key,
            base_url=kwargs.get("base_url", "https://integrate.api.nvidia.com/v1/embeddings"),
        )
    elif provider == "transformers":
        return TransformersEmbeddings(
            model_path=kwargs.get("model_path"),
            dim=kwargs.get("dim", 1024),
            device=kwargs.get("device"),
            max_length=kwargs.get("max_length", 512),
        )
    else:
        raise ValueError(
            f"不支持的嵌入 provider: {provider}\n"
            f"支持的 provider: nvidia, transformers"
        )


# ─────────────────────────────────────────
# 配置管理器
# ─────────────────────────────────────────
class EmbeddingConfig:
    """
    嵌入模型配置管理器

    支持从环境变量或显式参数加载配置。
    用于统一管理多个知识库的 embedding 配置。
    """

    # Provider 别名映射
    PROVIDER_ALIASES = {
        "cloud": "nvidia",
        "联网": "nvidia",
        "online": "nvidia",
        "local": "transformers",
        "本地": "transformers",
    }

    @classmethod
    def resolve_provider(cls, provider: str) -> str:
        """解析 provider 别名"""
        return cls.PROVIDER_ALIASES.get(provider.lower(), provider.lower())

    @classmethod
    def from_env(cls) -> dict:
        """从环境变量加载配置"""
        embed_provider = os.environ.get("RAG_EMBED_PROVIDER", "nvidia")
        return {
            "provider": cls.resolve_provider(embed_provider),
            "api_key": os.environ.get("NVIDIA_API_KEY", ""),
            "model": os.environ.get("RAG_EMBED_MODEL", "nvidia/nv-embed-v1"),
            "model_path": os.environ.get("RAG_EMBED_MODEL_PATH"),
            "base_url": os.environ.get("RAG_EMBED_BASE_URL"),
            "dim": int(os.environ.get("RAG_EMBED_DIM", "4096")),
        }

    @classmethod
    def create_model(cls, config: Optional[dict] = None, **overrides) -> EmbeddingModel:
        """
        根据配置创建嵌入模型

        Args:
            config: 配置字典，如果为 None 则从环境变量加载
            **overrides: 配置覆盖
        """
        if config is None:
            config = cls.from_env()

        config = {**config, **overrides}
        provider = cls.resolve_provider(config.get("provider", "nvidia"))

        kwargs = {}
        if config.get("model"):
            kwargs["model"] = config["model"]
        if config.get("model_path"):
            kwargs["model_path"] = config["model_path"]
        if config.get("base_url"):
            kwargs["base_url"] = config["base_url"]
        if config.get("dim"):
            kwargs["dim"] = config["dim"]

        return get_embedding_model(provider=provider, api_key=config.get("api_key"), **kwargs)
