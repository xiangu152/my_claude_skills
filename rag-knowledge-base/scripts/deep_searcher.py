#!/usr/bin/env python3
"""
Deep Searcher — 多跳深度检索器

支持：
  - Multi-Hop Retrieval：迭代多跳检索
  - Query Triggering：根据当前结果触发下一跳检索
  - Result Synthesis：合并多跳结果
"""

import sys
from typing import Optional, Callable

sys.path.insert(0, str(__file__).rsplit("/", 1)[0])

from llm import generate_text
from forest_retriever import ForestRetriever, RetrievedNode


# ─── Continuation Checker ──────────────────────────
def should_continue_hopping(
    query: str,
    results: list[RetrievedNode],
    context_window: int = 3,
    min_new_info_ratio: float = 0.3,
    **llm_kwargs,
) -> tuple[bool, str]:
    """判断是否需要继续多跳检索

    基于当前结果与原始查询的对比，判断是否需要继续检索。

    Args:
        query: 原始查询
        results: 当前检索结果
        context_window: 用于判断的上下文节点数
        min_new_info_ratio: 最小新信息比例
        **llm_kwargs: LLM 参数

    Returns:
        (是否继续, 判断理由)
    """
    if not results:
        return False, "无检索结果"

    # 检查结果数量
    if len(results) < context_window:
        return True, f"结果数量不足 ({len(results)} < {context_window})"

    # 检查距离分布
    distances = [r.distance for r in results]
    avg_distance = sum(distances) / len(distances)

    if avg_distance > 1.0:
        return True, f"平均距离过大 ({avg_distance:.2f})"

    # 使用 LLM 判断是否需要继续
    context = "\n".join([
        f"- {r.title}: {r.content[:150]}..."
        for r in results[:context_window]
    ])

    prompt = f"""判断以下检索结果是否足够回答用户的原始查询。

原始查询：{query}

当前检索结果：
{context}

请判断：
1. 这些结果是否足够回答原始查询？
2. 是否需要进一步检索获取更多信息？

输出格式：
继续检索: 是/否
理由: 简短说明（20字以内）
新触发查询: 如果需要继续，输出一句话描述需要检索什么（15字以内）

输出："""

    try:
        response = generate_text(prompt, max_tokens=128, **llm_kwargs)
        lines = response.strip().split("\n")

        should_continue = False
        reason = ""
        new_trigger = ""

        for line in lines:
            if "继续检索" in line or "是否" in line:
                should_continue = "是" in line or "继续" in line
            elif "理由" in line:
                reason = line.split("理由")[1].strip() if "理由" in line else ""
            elif "触发" in line or "查询" in line:
                new_trigger = line.split("触发")[1].split("查询")[0].strip() if "触发" in line else line.split("查询")[1].strip()

        return should_continue, reason, new_trigger

    except Exception:
        return False, "LLM 判断失败"


def generate_hop_trigger(
    query: str,
    results: list[RetrievedNode],
    **llm_kwargs,
) -> Optional[str]:
    """根据当前结果生成下一跳触发查询

    Args:
        query: 原始查询
        results: 当前检索结果
        **llm_kwargs: LLM 参数

    Returns:
        触发下一跳的查询，如果没有则返回 None
    """
    if not results:
        return None

    context = "\n".join([
        f"- {r.title}: {r.content[:200]}..."
        for r in results[:5]
    ])

    prompt = f"""基于原始查询和当前检索结果，生成一个进一步检索的查询。

原始查询：{query}

当前检索结果：
{context}

要求：
- 识别当前结果中的信息空白或需要深挖的点
- 生成一个具体的查询来填补这些空白
- 控制在 30 字以内
- 如果当前结果已经足够回答原始查询，返回空

进一步检索查询："""

    try:
        result = generate_text(prompt, max_tokens=64, **llm_kwargs)
        result = result.strip()
        # 如果结果为空或很短，返回 None
        if len(result) < 5:
            return None
        return result
    except Exception:
        return None


# ─── Deep Searcher ────────────────────────────────
class DeepSearcher:
    """深度搜索器"""

    def __init__(
        self,
        retriever: ForestRetriever,
        max_hops: int = 3,
        convergence_threshold: float = 0.8,
    ):
        """初始化深度搜索器

        Args:
            retriever: 森林检索器实例
            max_hops: 最大跳数
            convergence_threshold: 收敛阈值（当结果足够好时提前停止）
        """
        self.retriever = retriever
        self.max_hops = max_hops
        self.convergence_threshold = convergence_threshold

    def multi_hop_search(
        self,
        query: str,
        top_k: int = 10,
        expand_queries: bool = False,
        decompose_queries: bool = False,
        progress_callback: Optional[Callable[[int, list], None]] = None,
        **llm_kwargs,
    ) -> dict:
        """多跳检索主流程

        Args:
            query: 原始查询
            top_k: 每跳返回的结果数
            expand_queries: 是否启用查询扩展
            decompose_queries: 是否启用查询分解
            progress_callback: 进度回调函数 fn(hop, results)
            **llm_kwargs: LLM 参数

        Returns:
            {
                "original_query": str,
                "all_results": [RetrievedNode],
                "hop_history": [{"hop": int, "query": str, "results": [RetrievedNode]}],
                "total_hops": int,
            }
        """
        from query_rewrite import transform_query

        # 初始化
        all_results: dict[str, RetrievedNode] = {}  # node_id -> node
        hop_history = []

        # 初始查询处理
        current_queries = [query]

        if expand_queries or decompose_queries:
            transformed = transform_query(
                query,
                enable_expansion=expand_queries,
                enable_decomposition=decompose_queries,
                **llm_kwargs,
            )
            current_queries = transformed["all_queries"]

        # 第一跳
        for q in current_queries:
            results = self.retriever.retrieve(q, top_k=top_k)
            for node in results:
                if node.node_id not in all_results:
                    all_results[node.node_id] = node

            hop_history.append({
                "hop": 1,
                "query": q,
                "results": results,
            })

            if progress_callback:
                progress_callback(1, results)

        # 多跳迭代
        for hop in range(2, self.max_hops + 1):
            # 检查收敛
            current_results = list(all_results.values())
            avg_distance = sum(r.distance for r in current_results) / len(current_results)

            if avg_distance < self.convergence_threshold:
                print(f"  [Hop {hop}] 提前收敛 (avg_distance={avg_distance:.4f})")
                break

            # 生成触发查询
            trigger = generate_hop_trigger(query, current_results[:top_k], **llm_kwargs)

            if not trigger:
                print(f"  [Hop {hop}] 无触发查询，停止")
                break

            # 检查是否与已有查询重复
            if trigger in [h["query"] for h in hop_history]:
                print(f"  [Hop {hop}] 触发查询重复，停止: {trigger}")
                break

            print(f"  [Hop {hop}] 触发查询: {trigger}")

            # 执行检索
            results = self.retriever.retrieve(trigger, top_k=top_k)

            # 添加新结果
            new_count = 0
            for node in results:
                if node.node_id not in all_results:
                    all_results[node.node_id] = node
                    new_count += 1

            hop_history.append({
                "hop": hop,
                "query": trigger,
                "results": results,
            })

            if progress_callback:
                progress_callback(hop, results)

            # 如果没有新结果，停止
            if new_count == 0:
                print(f"  [Hop {hop}] 无新结果，停止")
                break

        return {
            "original_query": query,
            "all_results": list(all_results.values()),
            "hop_history": hop_history,
            "total_hops": len(hop_history),
        }

    def search(
        self,
        query: str,
        top_k: int = 10,
        **kwargs,
    ) -> list[RetrievedNode]:
        """简化的搜索入口"""
        result = self.multi_hop_search(query, top_k=top_k, **kwargs)
        return result["all_results"][:top_k]


# ─── Main ─────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="深度搜索测试")
    parser.add_argument("--kb-name", "-k", required=True)
    parser.add_argument("--query", "-q", required=True)
    parser.add_argument("--top-k", "-n", type=int, default=5)
    parser.add_argument("--max-hops", type=int, default=3)
    args = parser.parse_args()

    retriever = ForestRetriever(args.kb_name)
    searcher = DeepSearcher(retriever, max_hops=args.max_hops)

    print(f"\n开始深度搜索...")
    result = searcher.multi_hop_search(args.query, top_k=args.top_k)

    print(f"\n搜索完成：共 {result['total_hops']} 跳")
    print(f"检索到 {len(result['all_results'])} 个结果\n")

    for hop_info in result["hop_history"]:
        print(f"\n=== Hop {hop_info['hop']}: {hop_info['query']} ===")
        for node in hop_info["results"][:3]:
            print(f"  - {node.title} (dist={node.distance:.4f})")
