#!/usr/bin/env python3
"""
RAG 知识库查询脚本

整合了：
  - Query Rewrite：查询扩展与分解
  - Forest Retriever：森林结构检索
  - Deep Searcher：多跳深度检索

用法：
  # 基础检索
  python3 query_kb.py --kb-name my-kb --query "问题" --top-k 5

  # 启用查询扩展
  python3 query_kb.py --kb-name my-kb --query "问题" --expand

  # 启用查询分解
  python3 query_kb.py --kb-name my-kb --query "复杂问题" --decompose

  # 启用多跳深度检索
  python3 query_kb.py --kb-name my-kb --query "问题" --deep-search

  # 综合启用
  python3 query_kb.py --kb-name my-kb --query "问题" --expand --decompose --deep-search
"""
import os
import sys
import json
import argparse
from typing import Optional

sys.path.insert(0, str(__file__).rsplit("/", 1)[0])

from embeddings import EmbeddingConfig
from forest_retriever import ForestRetriever, RetrievedNode
from deep_searcher import DeepSearcher

KB_BASE = os.path.expanduser("~/.claude/knowledge_bases")


def query_kb(
    kb_name: str,
    query: str,
    top_k: int = 5,
    # Query Rewrite 选项
    expand: bool = False,
    decompose: bool = False,
    # Forest Retriever 选项
    enable_parent: bool = True,
    enable_siblings: bool = False,
    enable_subtree: bool = False,
    depth: int = 3,
    # Deep Search 选项
    deep_search: bool = False,
    max_hops: int = 3,
    # 输出选项
    verbose: bool = False,
) -> list[dict]:
    """查询知识库，返回检索结果

    Args:
        kb_name: 知识库名称
        query: 查询问题
        top_k: 返回结果数
        expand: 是否启用查询扩展
        decompose: 是否启用查询分解
        enable_parent: 是否启用父节点遍历
        enable_siblings: 是否启用兄弟节点扩展
        enable_subtree: 是否启用子树聚合
        depth: Top-Down 遍历深度
        deep_search: 是否启用多跳深度检索
        max_hops: 最大跳数
        verbose: 是否输出详细信息

    Returns:
        list of dicts: [{content, source, distance, title, level}, ...]
    """
    # 创建森林检索器
    retriever = ForestRetriever(kb_name)

    if verbose:
        print(f"[Query Rewrite] expand={expand}, decompose={decompose}")
        print(f"[Forest Retriever] parent={enable_parent}, siblings={enable_siblings}, subtree={enable_subtree}, depth={depth}")
        print(f"[Deep Searcher] enabled={deep_search}, max_hops={max_hops}")

    if deep_search:
        # 使用深度搜索
        searcher = DeepSearcher(retriever, max_hops=max_hops)

        if verbose:
            print(f"\n开始深度搜索...")

        result = searcher.multi_hop_search(
            query,
            top_k=top_k,
            expand_queries=expand,
            decompose_queries=decompose,
            progress_callback=lambda hop, results: print(f"  Hop {hop}: {len(results)} results"),
        )

        retrieved_nodes = result["all_results"]

        if verbose:
            print(f"\n深度搜索完成：共 {result['total_hops']} 跳，{len(retrieved_nodes)} 个结果")

    else:
        # 使用基础森林检索
        retrieved_nodes = retriever.retrieve(
            query,
            top_k=top_k,
            enable_parent=enable_parent,
            enable_siblings=enable_siblings,
            enable_subtree=enable_subtree,
            depth=depth,
        )

    # 转换为输出格式
    outputs = []
    for node in retrieved_nodes:
        outputs.append({
            "node_id": node.node_id,
            "title": node.title,
            "content": node.content,
            "source": node.source_file,
            "distance": node.distance,
            "level": node.level,
            "node_type": node.node_type,
        })

    return outputs


def main():
    parser = argparse.ArgumentParser(
        description="RAG 知识库查询",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 基础检索
  python3 query_kb.py -k my-kb -q "问题"

  # 启用查询扩展
  python3 query_kb.py -k my-kb -q "问题" --expand

  # 启用查询分解
  python3 query_kb.py -k my-kb -q "复杂问题" --decompose

  # 启用多跳深度检索
  python3 query_kb.py -k my-kb -q "问题" --deep-search

  # 综合启用
  python3 query_kb.py -k my-kb -q "问题" --expand --decompose --deep-search --verbose
""",
    )
    parser.add_argument("--kb-name", "-k", required=True, help="知识库名称")
    parser.add_argument("--query", "-q", required=True, help="查询问题")
    parser.add_argument("--top-k", "-n", type=int, default=5, help="返回片段数（默认 5）")

    # Query Rewrite 选项
    parser.add_argument("--expand", action="store_true", help="启用查询扩展")
    parser.add_argument("--decompose", action="store_true", help="启用查询分解")

    # Forest Retriever 选项
    parser.add_argument("--no-parent", action="store_true", help="禁用父节点遍历")
    parser.add_argument("--siblings", action="store_true", help="启用兄弟节点扩展")
    parser.add_argument("--subtree", action="store_true", help="启用子树聚合")
    parser.add_argument("--depth", type=int, default=3, help="Top-Down 遍历深度（默认 3）")

    # Deep Search 选项
    parser.add_argument("--deep-search", action="store_true", help="启用多跳深度检索")
    parser.add_argument("--max-hops", type=int, default=3, help="最大跳数（默认 3）")

    # 输出选项
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")

    args = parser.parse_args()

    results = query_kb(
        args.kb_name,
        args.query,
        top_k=args.top_k,
        expand=args.expand,
        decompose=args.decompose,
        enable_parent=not args.no_parent,
        enable_siblings=args.siblings,
        enable_subtree=args.subtree,
        depth=args.depth,
        deep_search=args.deep_search,
        max_hops=args.max_hops,
        verbose=args.verbose,
    )

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    print(f"\n检索到 {len(results)} 个结果：\n")
    for i, r in enumerate(results, 1):
        src = r["source"].replace(str(KB_BASE) + "/", "").replace(f"{args.kb_name}/", "")
        print(f"{'='*60}")
        print(f"[{i}] {r['title']} (Level {r['level']}, {r['node_type']})")
        print(f"来源: {src}")
        if r["distance"] is not None:
            print(f"相似度距离: {r['distance']:.4f}（越小越相关）")
        content = r["content"].strip()
        if len(content) > 500:
            content = content[:500] + "\n...（内容截断）"
        print(f"\n{content}\n")


if __name__ == "__main__":
    main()