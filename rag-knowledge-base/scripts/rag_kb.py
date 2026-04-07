#!/usr/bin/env python3
"""
RAG 知识库统一 CLI
用法: python rag_kb.py <command> [options]
"""

import sys
import argparse
from pathlib import Path

# 添入 scripts 目录确保导入路径
sys.path.insert(0, str(Path(__file__).parent))


def cmd_build(args):
    from build import build_knowledge_base
    build_knowledge_base(
        kb_name=args.name,
        input_path=args.input,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        embed_provider=args.embed_provider,
        embed_model=args.embed_model,
        show_progress=True,
    )


def cmd_query(args):
    from query import query_knowledge_base
    result = query_knowledge_base(
        kb_name=args.name,
        query_text=args.query,
        top_k=args.top_k,
        llm_model=args.llm_model,
        temperature=args.temperature,
        show_chunks=True,
    )
    print("\n=== 检索结果 ===")
    for i, chunk in enumerate(result.get("retrieved_chunks", []), 1):
        content = chunk["content"]
        meta = chunk["metadata"]
        print(f"\n[片段 {i}]")
        print(f"  标题: {meta.get('title', 'unknown')}")
        print(f"  来源: {meta.get('source', 'unknown')}")
        print(f"  内容: {content[:200]}{'...' if len(content) > 200 else ''}")

    print(f"\n=== LLM 回答（模型: {result['llm_model']}）===")
    print(result["answer"])


def cmd_manage(args):
    from manage import manage_knowledge_base
    result = manage_knowledge_base(
        kb_name=args.name,
        action=args.action,
        input_path=args.input,
        file_pattern=args.pattern,
    )
    print(f"结果: {result}")


def cmd_list(args):
    from manage import list_knowledge_bases
    kbs = list_knowledge_bases()
    if not kbs:
        print("尚未创建任何知识库。使用 build 命令构建第一个知识库。")
    else:
        print(f"共 {len(kbs)} 个知识库：\n")
        print(f"{'名称':<20} {'片段数':<10} {'嵌入模式':<10} {'模型':<30}")
        print("-" * 75)
        for kb in kbs:
            print(f"{kb['name']:<20} {kb['doc_count']:<10} {kb['embed_provider']:<10} {kb['embed_model']:<30}")


def main():
    parser = argparse.ArgumentParser(description="RAG 知识库工具（支持联网嵌入）")
    sub = parser.add_subparsers(dest="cmd", help="可用命令")

    # ── list ──────────────────────────────────────────────
    sub.add_parser("list", help="列出所有知识库")

    # ── build ──────────────────────────────────────────────
    b = sub.add_parser("build", help="从 md 文件构建知识库")
    b.add_argument("--name", "-n", required=True, help="知识库名称")
    b.add_argument("--input", "-i", required=True, help="输入文件或目录路径")
    b.add_argument("--chunk-size", type=int, default=500, help="文本分块大小（字符，默认 500）")
    b.add_argument("--chunk-overlap", type=int, default=50, help="分块重叠字符数（默认 50）")
    b.add_argument("--embed-provider", default="nvidia",
                   choices=["nvidia", "transformers"],
                   help="嵌入模式: nvidia=联网（默认）, transformers=本地模型")
    b.add_argument("--embed-model", default="nvidia/nv-embed-v1",
                   help="嵌入模型（nvidia 默认 nvidia/nv-embed-v1）")

    # ── query ──────────────────────────────────────────────
    q = sub.add_parser("query", help="查询知识库")
    q.add_argument("--name", "-n", required=True, help="知识库名称")
    q.add_argument("--query", "-q", required=True, help="查询问题")
    q.add_argument("--top-k", type=int, default=5, help="返回最相似的片段数（默认 5）")
    q.add_argument("--llm-model", default="gpt-4o-mini", help="LLM 模型")
    q.add_argument("--temperature", type=float, default=0.3, help="LLM 温度（默认 0.3）")

    # ── manage ─────────────────────────────────────────────
    m = sub.add_parser("manage", help="管理知识库")
    m.add_argument("--name", "-n", required=True, help="知识库名称")
    m.add_argument("--action", "-a", required=True,
                   choices=["add", "remove", "stats", "clear"],
                   help="操作: add=添加文档, remove=删除知识库, stats=统计, clear=清空")
    m.add_argument("--input", "-i", help="输入文件或目录（add 时需要）")
    m.add_argument("--pattern", default="*.md", help="文件匹配模式")

    args = parser.parse_args()

    if args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "build":
        cmd_build(args)
    elif args.cmd == "query":
        cmd_query(args)
    elif args.cmd == "manage":
        cmd_manage(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
