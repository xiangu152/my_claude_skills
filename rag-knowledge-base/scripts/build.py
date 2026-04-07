#!/usr/bin/env python3
"""
构建知识库：加载 md 文件 → 分块 → 向量化 → 存入 ChromaDB
支持 nvidia（联网）和 transformers（本地）两种嵌入模式
"""

import json
import os
from pathlib import Path
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from embeddings import get_embedding_model


def _get_kb_dir(kb_name: str) -> Path:
    base = Path.home() / ".claude" / "knowledge_bases"
    return base / kb_name


def _get_chroma_path(kb_name: str) -> Path:
    return _get_kb_dir(kb_name) / "chroma"


def _get_meta_path(kb_name: str) -> Path:
    return _get_kb_dir(kb_name) / "metadata.json"


def _load_markdown_files(input_path: str) -> list[Document]:
    """加载 md 文件或目录下的所有 md 文件"""
    path = Path(input_path)
    docs = []

    if path.is_file():
        files = [path]
    else:
        files = list(path.rglob("*.md"))

    if not files:
        raise FileNotFoundError(f"未找到任何 .md 文件: {input_path}")

    for f in files:
        try:
            content = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = f.read_text(encoding="gbk")
        title = f.stem
        metadata = {
            "source": str(f),
            "title": title,
            "type": "directory" if path.is_dir() else "file",
        }
        docs.append(Document(page_content=content, metadata=metadata))

    return docs


def build_knowledge_base(
    kb_name: str,
    input_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    embed_provider: str = "nvidia",
    embed_model: str = "nvidia/nv-embed-v1",
    show_progress: bool = True,
) -> dict:
    """
    从 markdown 文件构建知识库

    Args:
        kb_name: 知识库名称
        input_path: md 文件或目录路径
        chunk_size: 文本分块大小（字符）
        chunk_overlap: 分块重叠字符数
        embed_provider: "nvidia"（联网）或 "transformers"（本地）
        embed_model: 嵌入模型名
        show_progress: 是否显示进度
    """
    kb_dir = _get_kb_dir(kb_name)
    kb_dir.mkdir(parents=True, exist_ok=True)
    chroma_path = _get_chroma_path(kb_name)

    # 1. 加载文档
    if show_progress:
        print(f"[1/4] 加载 markdown 文件...")
    docs = _load_markdown_files(input_path)
    if show_progress:
        print(f"  加载了 {len(docs)} 个文件")

    # 2. 文本分块
    if show_progress:
        print(f"[2/4] 分块（chunk_size={chunk_size}, overlap={chunk_overlap}）...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
    )
    chunks = splitter.split_documents(docs)
    if show_progress:
        print(f"  切分为 {len(chunks)} 个文本片段")

    # 3. 向量化并存入 ChromaDB
    if show_progress:
        provider_label = "NVIDIA NIM（联网）" if embed_provider == "nvidia" else f"Transformers {embed_model}（本地）"
        print(f"[3/4] 向量化并存储（{provider_label}）...")

    # 删除旧的向量库
    import shutil
    if chroma_path.exists():
        shutil.rmtree(chroma_path)

    # 获取嵌入模型
    embeddings = get_embedding_model(provider=embed_provider, model=embed_model)

    # 手动批量嵌入然后存入 ChromaDB（因为用了自定义 Embedding 类）
    from langchain_chroma import Chroma

    vectorstore = Chroma(
        persist_directory=str(chroma_path),
        embedding_function=embeddings,
        collection_name=kb_name,
    )
    vectorstore.add_documents(chunks)
    if show_progress:
        print(f"  已存入向量数据库: {chroma_path}")

    # 4. 保存元数据
    source_files = []
    if Path(input_path).is_dir():
        source_files = [str(f) for f in Path(input_path).rglob("*.md")]
    else:
        source_files = [str(Path(input_path))]

    meta = {
        "kb_name": kb_name,
        "kb_dir": str(kb_dir),
        "chroma_path": str(chroma_path),
        "doc_count": len(chunks),
        "source_files": source_files,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "embed_provider": embed_provider,
        "embed_model": embed_model,
        "llm_model": "qwen2.5:7b",
    }
    with open(_get_meta_path(kb_name), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    if show_progress:
        print(f"[4/4] 完成！知识库 '{kb_name}' 构建成功，共 {len(chunks)} 个片段。")

    return meta
