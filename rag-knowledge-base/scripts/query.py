#!/usr/bin/env python3
"""
查询知识库：向量化问题 → 检索相似片段 → LLM 生成回答
支持 nvidia（联网）和 transformers（本地）两种嵌入模式
"""

import json
from pathlib import Path
from typing import Optional

from langchain_chroma import Chroma

from embeddings import get_embedding_model
from llm import generate_text


DEFAULT_PROMPT = """你是一个专业的知识库问答助手。请根据以下参考材料回答用户的问题。

如果参考材料中有明确答案，请基于参考材料回答，并标注来源。
如果参考材料不足以回答，请如实说明，不要编造。

参考材料：
{context}

用户问题：{question}

回答："""


def _load_kb_meta(kb_name: str) -> dict:
    meta_path = Path.home() / ".claude" / "knowledge_bases" / kb_name / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"知识库 '{kb_name}' 不存在。请先使用 build 命令构建。")
    with open(meta_path, encoding="utf-8") as f:
        return json.load(f)


def query_knowledge_base(
    kb_name: str,
    query_text: str,
    top_k: int = 5,
    llm_model: str = "gpt-4o-mini",
    temperature: float = 0.3,
    embed_provider: Optional[str] = None,
    embed_model: Optional[str] = None,
    prompt_template: Optional[str] = None,
    show_chunks: bool = True,
) -> dict:
    """
    查询知识库

    Args:
        kb_name: 知识库名称
        query_text: 查询问题
        top_k: 返回最相似的片段数
        llm_model: LLM 模型名（默认 gpt-4o-mini）
        temperature: LLM 温度（0=精确，1=发散）
        embed_provider: 嵌入模式，默认从知识库元数据读取
        embed_model: 嵌入模型，默认从知识库元数据读取
        prompt_template: 自定义 Prompt
        show_chunks: 是否返回检索片段
    """
    meta = _load_kb_meta(kb_name)
    chroma_path = meta["chroma_path"]
    embed_provider = embed_provider or meta.get("embed_provider", "nvidia")
    embed_model = embed_model or meta.get("embed_model", "nvidia/nv-embed-v1")

    # 构建检索器
    embeddings = get_embedding_model(provider=embed_provider, model=embed_model)
    vectorstore = Chroma(
        persist_directory=chroma_path,
        embedding_function=embeddings,
        collection_name=kb_name,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    retrieved = retriever.invoke(query_text)

    # 组装上下文
    context_parts = []
    for i, doc in enumerate(retrieved, 1):
        source = doc.metadata.get("source", "unknown")
        title = doc.metadata.get("title", "")
        context_parts.append(f"[{i}] {title}\n来源: {source}\n{doc.page_content}")

    context_str = "\n\n".join(context_parts)
    prompt_text = prompt_template or DEFAULT_PROMPT

    # 调用 LLM
    formatted_prompt = prompt_text.format(context=context_str, question=query_text)
    answer = generate_text(formatted_prompt, max_tokens=1024, temperature=temperature, model=llm_model)

    result = {
        "answer": answer,
        "query": query_text,
        "llm_model": llm_model,
        "embed_provider": embed_provider,
        "embed_model": embed_model,
    }

    if show_chunks:
        result["retrieved_chunks"] = [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in retrieved
        ]

    return result
