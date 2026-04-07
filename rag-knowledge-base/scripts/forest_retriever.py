#!/usr/bin/env python3
"""
Forest Retriever — 森林检索器

利用森林结构进行多层次、多策略的检索。

检索策略：
  - Top-Down Traversal：从根节点向下聚焦
  - Parent Traversal：收集祖先节点获取上下文
  - Siblings Expansion：探索兄弟节点
  - Subtree Aggregation：聚合子树形成完整上下文
"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(__file__).rsplit("/", 1)[0])

import chromadb

from embeddings import EmbeddingConfig, EmbeddingModel


@dataclass
class RetrievedNode:
    """检索结果节点"""
    node_id: str
    title: str
    content: str
    abstract: str
    level: int
    source_file: str
    node_type: str
    distance: float = 0.0
    has_children: bool = False
    parent_id: Optional[str] = None
    score: float = 0.0  # 综合评分


class ForestRetriever:
    """森林检索器"""

    def __init__(
        self,
        kb_name: str,
        embed_model: Optional[EmbeddingModel] = None,
        embed_config: Optional[dict] = None,
    ):
        """初始化森林检索器

        Args:
            kb_name: 知识库名称
            embed_model: 嵌入模型实例（如果为 None，从 embed_config 创建）
            embed_config: 嵌入模型配置（当 embed_model 为 None 时使用）
        """
        self.kb_name = kb_name
        self.kb_path = Path.home() / ".claude" / "knowledge_bases" / kb_name

        # 读取森林元数据
        meta_path = self.kb_path / "forest" / "forest_meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"知识库 '{kb_name}' 不存在或未构建森林索引")

        with open(meta_path, encoding="utf-8") as f:
            self.meta = json.load(f)

        self.chroma_path = self.meta["chroma_path"]
        self.embedding_dim = self.meta.get("embedding_dim", 4096)

        # 加载节点元数据
        nodes_meta_path = self.kb_path / "forest" / "nodes_meta.json"
        if nodes_meta_path.exists():
            with open(nodes_meta_path, encoding="utf-8") as f:
                self.nodes_meta: dict = json.load(f)
        else:
            self.nodes_meta = {}

        # 初始化嵌入模型
        if embed_model is None:
            if embed_config is None:
                embed_config = {
                    "provider": self.meta.get("embed_api", "nvidia"),
                    "api_key": os.environ.get("NVIDIA_API_KEY", ""),
                    "model": self.meta.get("embed_model", ""),
                }
            self.embed_model = EmbeddingConfig.create_model(embed_config)
        else:
            self.embed_model = embed_model

        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=f"{kb_name}_forest"
        )

    # ─── 基础检索 ─────────────────────────────────────

    def _basic_retrieve(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[RetrievedNode]:
        """基础向量检索，返回 Top-K 结果"""
        query_emb = self.embed_model.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        for i in range(len(results["documents"][0])):
            meta = results["metadatas"][0][i] or {}
            retrieved.append(RetrievedNode(
                node_id=meta.get("node_id", ""),
                title=meta.get("title", ""),
                content=results["documents"][0][i],
                abstract="",
                level=meta.get("level", 1),
                source_file=meta.get("source", ""),
                node_type=meta.get("node_type", "content"),
                distance=results["distances"][0][i] if results["distances"] else 0.0,
                has_children=meta.get("has_children", False),
                parent_id=self.nodes_meta.get(meta.get("node_id", {}), {}).get("parent_id"),
            ))

        return retrieved

    # ─── Top-Down Traversal ────────────────────────────

    def top_down_traverse(
        self,
        query: str,
        depth: int = 3,
        top_k_per_level: int = 5,
    ) -> list[RetrievedNode]:
        """自顶向下遍历

        从根节点开始，逐层向下聚焦相关分支。

        Args:
            query: 查询
            depth: 最大深度（0 = 只看根节点）
            top_k_per_level: 每层返回的最大节点数

        Returns:
            检索结果列表
        """
        # 第一步：获取根节点级别的粗检索
        root_level = 1
        all_results = []

        # 初始检索，获取候选节点
        candidates = self._basic_retrieve(query, top_k=top_k_per_level * 2)

        if not candidates:
            return []

        # 按层级收集
        level_results = {1: []}
        for node in candidates:
            if node.level not in level_results:
                level_results[node.level] = []
            level_results[node.level].append(node)

        # 如果 depth > 0，继续向下探索子节点
        if depth > 1:
            for node in candidates[:top_k_per_level]:
                if node.has_children:
                    # 检索该节点的子节点
                    child_query = f"{node.title} {query}"
                    children = self._basic_retrieve(child_query, top_k=top_k_per_level)
                    level_results.setdefault(node.level + 1, []).extend(children)

        # 合并所有层级的结果
        for level in sorted(level_results.keys()):
            if level <= depth:
                all_results.extend(level_results[level][:top_k_per_level])

        # 去重
        seen = set()
        unique_results = []
        for node in all_results:
            if node.node_id not in seen:
                seen.add(node.node_id)
                unique_results.append(node)

        return unique_results[:top_k_per_level * depth]

    # ─── Parent Traversal ───────────────────────────────

    def parent_traversal(
        self,
        nodes: list[RetrievedNode],
        max_ancestors: int = 3,
    ) -> list[RetrievedNode]:
        """父节点遍历

        对每个检索到的节点，收集其祖先节点以获取更多上下文。

        Args:
            nodes: 初始检索结果
            max_ancestors: 最大祖先深度

        Returns:
            包含祖先节点的结果列表
        """
        if not nodes:
            return []

        # 构建 node_id -> node 的映射
        node_map = {n.node_id: n for n in nodes}
        ancestor_ids = set()

        # 对每个节点，收集祖先
        for node in nodes:
            if not node.node_id:
                continue

            # 从元数据中获取祖先链
            current_id = node.node_id
            depth = 0

            while depth < max_ancestors:
                node_meta = self.nodes_meta.get(current_id, {})
                parent_id = node_meta.get("parent_id")

                if not parent_id or parent_id in ancestor_ids:
                    break

                ancestor_ids.add(parent_id)
                current_id = parent_id
                depth += 1

        # 批量检索祖先节点
        if ancestor_ids:
            results = self.collection.get(
                ids=list(ancestor_ids),
                include=["documents", "metadatas"],
            )

            for i, node_id in enumerate(results["ids"]):
                meta = results["metadatas"][i] or {}
                ancestor = RetrievedNode(
                    node_id=node_id,
                    title=meta.get("title", ""),
                    content=results["documents"][i],
                    abstract="",
                    level=meta.get("level", 1),
                    source_file=meta.get("source", ""),
                    node_type=meta.get("node_type", "content"),
                    distance=0.0,  # 祖先节点不计算距离
                    has_children=meta.get("has_children", False),
                    parent_id=meta.get("parent_id"),
                )
                if ancestor.node_id not in node_map:
                    node_map[ancestor.node_id] = ancestor

        # 按 level 排序返回
        return sorted(node_map.values(), key=lambda n: n.level)

    # ─── Siblings Expansion ───────────────────────────

    def siblings_expansion(
        self,
        nodes: list[RetrievedNode],
        max_siblings_per_node: int = 2,
    ) -> list[RetrievedNode]:
        """兄弟节点扩展

        对每个检索到的节点，探索其兄弟节点（同一父节点下的其他子节点）。

        Args:
            nodes: 初始检索结果
            max_siblings_per_node: 每个节点最多扩展的兄弟数

        Returns:
            包含兄弟节点的结果列表
        """
        if not nodes:
            return []

        # 收集父节点 ID
        parent_to_children: dict[str, list[str]] = {}
        for node in nodes:
            if node.parent_id:
                parent_to_children.setdefault(node.parent_id, []).append(node.node_id)

        sibling_ids = set()

        # 对每个父节点，找到所有子节点（除了已检索的）
        for parent_id, child_ids in parent_to_children.items():
            parent_meta = self.nodes_meta.get(parent_id, {})
            siblings = parent_meta.get("child_ids", [])

            # 排除已检索的节点
            for sibling_id in siblings:
                if sibling_id not in child_ids:
                    sibling_ids.add(sibling_id)

        if not sibling_ids:
            return nodes

        # 批量检索兄弟节点
        results = self.collection.get(
            ids=list(sibling_ids),
            include=["documents", "metadatas"],
        )

        # 添加兄弟节点到结果
        node_map = {n.node_id: n for n in nodes}

        for i, node_id in enumerate(results["ids"]):
            meta = results["metadatas"][i] or {}
            sibling = RetrievedNode(
                node_id=node_id,
                title=meta.get("title", ""),
                content=results["documents"][i],
                abstract="",
                level=meta.get("level", 1),
                source_file=meta.get("source", ""),
                node_type=meta.get("node_type", "content"),
                distance=0.0,
                has_children=meta.get("has_children", False),
                parent_id=meta.get("parent_id"),
            )
            if sibling.node_id not in node_map:
                node_map[sibling.node_id] = sibling

        return list(node_map.values())

    # ─── Subtree Aggregation ─────────────────────────

    def subtree_aggregation(
        self,
        nodes: list[RetrievedNode],
        max_nodes_per_subtree: int = 10,
    ) -> list[RetrievedNode]:
        """子树聚合

        对每个节点，聚合其子树中的所有节点，形成完整的上下文。

        Args:
            nodes: 初始检索结果
            max_nodes_per_subtree: 每个子树最多收集的节点数

        Returns:
            聚合后的结果列表
        """
        if not nodes:
            return []

        # 收集所有相关的 node_id（包括子树）
        all_node_ids = set()

        for node in nodes:
            if node.node_id:
                all_node_ids.add(node.node_id)

                # 收集子树
                node_meta = self.nodes_meta.get(node.node_id, {})
                subtree_ids = self._collect_subtree(node.node_id, max_nodes_per_subtree)
                all_node_ids.update(subtree_ids)

        # 批量检索
        results = self.collection.get(
            ids=list(all_node_ids),
            include=["documents", "metadatas"],
        )

        # 构建结果
        node_map = {}
        for i, node_id in enumerate(results["ids"]):
            meta = results["metadatas"][i] or {}
            retrieved = RetrievedNode(
                node_id=node_id,
                title=meta.get("title", ""),
                content=results["documents"][i],
                abstract="",
                level=meta.get("level", 1),
                source_file=meta.get("source", ""),
                node_type=meta.get("node_type", "content"),
                distance=0.0,
                has_children=meta.get("has_children", False),
                parent_id=meta.get("parent_id"),
            )
            node_map[node_id] = retrieved

        # 按 level 排序，优先返回浅层节点
        return sorted(node_map.values(), key=lambda n: (n.level, n.distance))

    def _collect_subtree(
        self,
        node_id: str,
        max_nodes: int,
        collected: Optional[set] = None,
    ) -> set:
        """递归收集子树节点"""
        if collected is None:
            collected = set()

        if len(collected) >= max_nodes:
            return collected

        node_meta = self.nodes_meta.get(node_id, {})
        child_ids = node_meta.get("child_ids", [])

        for child_id in child_ids:
            if child_id not in collected:
                collected.add(child_id)
                if len(collected) >= max_nodes:
                    return collected
                # 递归收集
                self._collect_subtree(child_id, max_nodes, collected)

        return collected

    # ─── Main Retrieve ───────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        enable_parent: bool = True,
        enable_siblings: bool = False,
        enable_subtree: bool = False,
        depth: int = 3,
    ) -> list[RetrievedNode]:
        """综合检索入口

        Args:
            query: 查询
            top_k: 返回的最大结果数
            enable_parent: 是否启用父节点遍历
            enable_siblings: 是否启用兄弟节点扩展
            enable_subtree: 是否启用子树聚合
            depth: Top-Down 遍历深度

        Returns:
            检索结果列表
        """
        # Step 1: 基础检索 + Top-Down
        results = self.top_down_traverse(query, depth=depth, top_k_per_level=top_k)

        if not results:
            return []

        # Step 2: Parent Traversal
        if enable_parent:
            results = self.parent_traversal(results)

        # Step 3: Siblings Expansion
        if enable_siblings:
            results = self.siblings_expansion(results)

        # Step 4: Subtree Aggregation
        if enable_subtree:
            results = self.subtree_aggregation(results)

        # 最终截取 top_k
        return results[:top_k]


# ─── Main ─────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="森林检索测试")
    parser.add_argument("--kb-name", "-k", required=True)
    parser.add_argument("--query", "-q", required=True)
    parser.add_argument("--top-k", "-n", type=int, default=5)
    args = parser.parse_args()

    retriever = ForestRetriever(args.kb_name)
    results = retriever.retrieve(args.query, top_k=args.top_k)

    print(f"\n检索到 {len(results)} 个结果：\n")
    for i, node in enumerate(results, 1):
        print(f"{'='*60}")
        print(f"[{i}] {node.title} (Level {node.level})")
        print(f"    ID: {node.node_id}")
        print(f"    Distance: {node.distance:.4f}")
        print(f"    Source: {node.source_file}")
        content = node.content[:200] + "..." if len(node.content) > 200 else node.content
        print(f"    Content: {content}")
