#!/usr/bin/env python3
"""
Query Rewrite Module — 查询改写模块

提供：
  - Query Expansion：同义词扩展，生成多个查询变体
  - Query Decomposition：分解复杂问题为多个子问题

这些技术帮助弥合用户问题与文档内容之间的语义鸿沟。
"""

import sys
from typing import Optional

sys.path.insert(0, str(__file__).rsplit("/", 1)[0])

from llm import generate_text


# ─── Query Expansion ─────────────────────────────────
def expand_query(
    query: str,
    n: int = 3,
    style: str = "variations",
    **llm_kwargs,
) -> list[str]:
    """扩展查询，生成多个同义词/不同表述的变体

    Args:
        query: 原始查询
        n: 生成变体数量
        style: 扩展风格
            - "variations": 不同表述方式
            - "synonyms": 同义词替换
            - "broader": 更广泛的表述
            - "narrower": 更具体的表述
        **llm_kwargs: 传递给 LLM 的参数

    Returns:
        扩展后的查询列表

    Example:
        >>> expand_query("如何戒烟")
        ["怎样戒烟最有效", "戒烟的好方法有哪些", "快速戒烟技巧"]
    """
    prompt = f"""将以下查询扩展为 {n} 个不同的变体，覆盖同义词、不同表述角度。

要求：
- 每行一个查询
- 控制在 15-40 字
- 只输出查询内容，不要编号、不要解释

风格：{style}

原始查询：{query}

扩展查询："""

    try:
        result = generate_text(prompt, max_tokens=256, **llm_kwargs)
        queries = [q.strip() for q in result.split("\n") if q.strip()]
        return queries[:n]
    except Exception:
        return [query]


# ─── Query Decomposition ─────────────────────────────
def decompose_query(
    query: str,
    max_subqueries: int = 5,
    **llm_kwargs,
) -> list[str]:
    """分解复杂问题为多个可独立检索的子问题

    Args:
        query: 原始复杂查询
        max_subqueries: 最大子问题数量
        **llm_kwargs: 传递给 LLM 的参数

    Returns:
        子问题列表

    Example:
        >>> decompose_query("微软和谷歌去年谁赚得多？")
        ["微软去年净利润是多少？", "谷歌去年净利润是多少？", "两家公司利润对比"]
    """
    prompt = f"""将以下复杂问题分解为多个简单的子问题（每个子问题可独立检索）。

要求：
- 每个子问题必须是独立的、可直接检索的
- 每行一个子问题
- 控制在 15-40 字
- 只输出子问题，不要编号、不要解释
- 最多 {max_subqueries} 个子问题

复杂问题：{query}

子问题："""

    try:
        result = generate_text(prompt, max_tokens=512, **llm_kwargs)
        subqueries = [q.strip() for q in result.split("\n") if q.strip()]
        return subqueries[:max_subqueries]
    except Exception:
        return [query]


# ─── Step-Back Prompting ───────────────────────────
def step_back_query(
    query: str,
    **llm_kwargs,
) -> str:
    """退后一步，将问题抽象化

    当直接检索效果不好时，先抽象到更高层次，获取更广泛的上下文。

    Args:
        query: 原始查询
        **llm_kwargs: 传递给 LLM 的参数

    Returns:
        抽象后的查询

    Example:
        >>> step_back_query("如何在30天内戒除20年烟瘾？")
        "烟草依赖的治疗方法"
    """
    prompt = f"""将以下问题抽象为一个更高层次的概念，以便进行更广泛的检索。

要求：
- 输出一句话概括核心主题
- 控制在 20 字以内
- 只输出抽象查询，不要解释

原始问题：{query}

抽象查询："""

    try:
        result = generate_text(prompt, max_tokens=64, **llm_kwargs)
        return result.strip()
    except Exception:
        return query


# ─── Combined Query Transform ───────────────────────
def transform_query(
    query: str,
    enable_expansion: bool = True,
    enable_decomposition: bool = True,
    expansion_count: int = 3,
    max_subqueries: int = 5,
    **llm_kwargs,
) -> dict:
    """综合查询转换

    同时执行扩展和分解，返回结构化的转换结果。

    Args:
        query: 原始查询
        enable_expansion: 是否启用扩展
        enable_decomposition: 是否启用分解
        expansion_count: 扩展变体数量
        max_subqueries: 最大子问题数量
        **llm_kwargs: 传递给 LLM 的参数

    Returns:
        {
            "original": str,           # 原始查询
            "expanded": [str],         # 扩展查询列表
            "decomposed": [str],       # 子问题列表
            "all_queries": [str],      # 所有待检索的查询
        }
    """
    result = {
        "original": query,
        "expanded": [],
        "decomposed": [],
        "all_queries": [query],  # 原始查询始终保留
    }

    if enable_expansion:
        try:
            result["expanded"] = expand_query(query, n=expansion_count, **llm_kwargs)
            result["all_queries"].extend(result["expanded"])
        except Exception:
            pass

    if enable_decomposition:
        try:
            result["decomposed"] = decompose_query(query, max_subqueries, **llm_kwargs)
            # 去重后添加
            for q in result["decomposed"]:
                if q not in result["all_queries"]:
                    result["all_queries"].append(q)
        except Exception:
            pass

    return result


# ─── Main ─────────────────────────────────────────
if __name__ == "__main__":
    import json

    # Test
    query = "微软和谷歌去年谁赚得多？"

    print(f"原始查询: {query}\n")

    # Expansion
    expanded = expand_query(query)
    print(f"扩展查询: {expanded}\n")

    # Decomposition
    decomposed = decompose_query(query)
    print(f"分解子问题: {decomposed}\n")

    # Combined
    transformed = transform_query(query)
    print(f"综合转换: {json.dumps(transformed, ensure_ascii=False, indent=2)}\n")