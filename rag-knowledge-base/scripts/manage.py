#!/usr/bin/env python3
"""
管理知识库：列出 / 添加 / 删除 / 统计
"""

import json
import shutil
from pathlib import Path
from typing import Optional

from langchain_chroma import Chroma

from embeddings import get_embedding_model


def _kb_base_dir() -> Path:
    return Path.home() / ".claude" / "knowledge_bases"


def _get_kb_meta(kb_name: str) -> dict:
    meta_path = _kb_base_dir() / kb_name / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"知识库 '{kb_name}' 不存在")
    with open(meta_path, encoding="utf-8") as f:
        return json.load(f)


def _save_kb_meta(meta: dict):
    kb_name = meta["kb_name"]
    meta_path = _kb_base_dir() / kb_name / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def list_knowledge_bases() -> list[dict]:
    """列出所有已创建的知识库"""
    base = _kb_base_dir()
    if not base.exists():
        return []

    kbs = []
    for kb_dir in base.iterdir():
        meta_path = kb_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
                kbs.append({
                    "name": meta["kb_name"],
                    "doc_count": meta.get("doc_count", 0),
                    "embed_provider": meta.get("embed_provider", "unknown"),
                    "embed_model": meta.get("embed_model", "unknown"),
                    "source_files": len(meta.get("source_files", [])),
                })
    return kbs


def add_to_knowledge_base(
    kb_name: str,
    input_path: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> dict:
    """向已有知识库添加文档"""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from build import _load_markdown_files

    meta = _get_kb_meta(kb_name)
    chroma_path = meta["chroma_path"]
    embed_provider = meta.get("embed_provider", "nvidia")
    embed_model = meta.get("embed_model", "BAAI/bge-m3")

    new_docs = _load_markdown_files(input_path)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=True,
    )
    new_chunks = splitter.split_documents(new_docs)

    embeddings = get_embedding_model(provider=embed_provider, model=embed_model)
    vectorstore = Chroma(
        persist_directory=chroma_path,
        embedding_function=embeddings,
        collection_name=kb_name,
    )
    vectorstore.add_documents(new_chunks)

    meta["doc_count"] = len(new_chunks) + meta.get("doc_count", 0)
    existing_files = set(meta.get("source_files", []))
    new_files = []
    if Path(input_path).is_dir():
        new_files = [str(f) for f in Path(input_path).rglob("*.md")]
    else:
        new_files = [str(Path(input_path))]
    meta["source_files"] = list(existing_files | set(new_files))
    _save_kb_meta(meta)

    return {"added_chunks": len(new_chunks), "total_chunks": meta["doc_count"]}


def remove_knowledge_base(kb_name: str) -> dict:
    """删除整个知识库"""
    kb_dir = _kb_base_dir() / kb_name
    if not kb_dir.exists():
        raise FileNotFoundError(f"知识库 '{kb_name}' 不存在")
    shutil.rmtree(kb_dir)
    return {"deleted": kb_name}


def kb_stats(kb_name: str) -> dict:
    """查看知识库统计信息"""
    meta = _get_kb_meta(kb_name)
    return {
        "name": meta["kb_name"],
        "doc_count": meta.get("doc_count", 0),
        "embed_provider": meta.get("embed_provider", "unknown"),
        "embed_model": meta.get("embed_model", "unknown"),
        "chunk_size": meta.get("chunk_size", 0),
        "chunk_overlap": meta.get("chunk_overlap", 0),
        "source_files": meta.get("source_files", []),
        "chroma_path": meta.get("chroma_path", ""),
    }


def manage_knowledge_base(
    kb_name: str,
    action: str,
    input_path: Optional[str] = None,
    file_pattern: str = "*.md",
) -> dict:
    if action == "add":
        if not input_path:
            raise ValueError("add 操作需要指定 --input 参数")
        return add_to_knowledge_base(kb_name, input_path)
    elif action == "remove":
        return remove_knowledge_base(kb_name)
    elif action == "stats":
        return kb_stats(kb_name)
    elif action == "clear":
        kb_dir = _kb_base_dir() / kb_name
        if kb_dir.exists():
            shutil.rmtree(kb_dir)
        return {"cleared": kb_name}
    else:
        raise ValueError(f"未知操作: {action}")
