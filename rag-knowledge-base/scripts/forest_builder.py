#!/usr/bin/env python3
"""
Forest Index Builder — 将 LLM 解析输出的森林 JSON 构建为索引

核心思想：
  - 森林结构由 LLM 解析任意格式文档输出为 JSON
  - 本脚本只负责加载 JSON、生成摘要、向量化、存储
  - 解析器与索引器分离，适配任意文档格式

用法：
    python3 forest_builder.py --kb-name my-kb --forest-json ./forest.json
"""
import os
import sys
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from pathlib import Path

# 确保导入路径正确
sys.path.insert(0, str(__file__).rsplit("/", 1)[0])

from embeddings import EmbeddingConfig, EmbeddingModel
from llm import LLMThreadPool, generate_abstract, LLM_MODEL, LLM_BASE_URL


# ─── 树节点数据结构 ─────────────────────────────
@dataclass
class ForestNode:
    node_id: str
    title: str
    level: int
    content: str
    abstract: str = ""
    source_file: str = ""
    parent_id: Optional[str] = None
    child_ids: list = field(default_factory=list)
    embedding: Optional[list] = None
    node_type: str = "content"


# ─── 森林嵌入器（使用统一 embeddings.py）──────────────
class ForestIndexer:
    """向量嵌入（使用统一的 EmbeddingModel 接口）"""

    def __init__(self, embed_model: EmbeddingModel):
        """初始化嵌入器

        Args:
            embed_model: EmbeddingModel 实例（从 embeddings.py 创建）
        """
        self.embed_model = embed_model
        self.DIM = embed_model.DIM
        self.EMBED_MODEL = embed_model.MODEL_NAME
        self._cache: dict[str, list] = {}

    def _embed(self, text: str) -> list[float]:
        """单条嵌入（带缓存）"""
        if not text.strip():
            return [0.0] * self.DIM
        if text in self._cache:
            return self._cache[text]
        emb = self.embed_model.embed_query(text)
        self._cache[text] = emb
        return emb

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入"""
        items = [(i, t) for i, t in enumerate(texts) if t.strip()]
        if not items:
            return [[0.0] * self.DIM for _ in texts]

        raw_texts = [t for _, t in items]
        embs = self.embed_model.embed_documents(raw_texts)

        out: list[list[float]] = [[0.0] * self.DIM for _ in texts]
        for (i, _), emb in zip(items, embs):
            out[i] = emb
        return out

    def index(self, nodes: dict[str, ForestNode],
             generate_abstracts: bool = True,
             llm_workers: int = 8,
             checkpoint_every: int = 16,
             checkpoint_store=None):
        """生成语义摘要 + 嵌入向量

        Args:
            checkpoint_every: 每多少个节点保存一次 checkpoint（默认16）
            checkpoint_store: ForestStore 实例，用于保存 checkpoint
        """
        node_list = list(nodes.values())
        total = len(node_list)

        if generate_abstracts:
            print(f"\n  生成语义摘要（{total} 个节点，{llm_workers} 并发，每 {checkpoint_every} 节点checkpoint）...")
            pool = LLMThreadPool(max_workers=llm_workers)

            # 收集需要生成摘要的节点（跳过已有摘要的，支持断点续传）
            to_generate = [(i, node) for i, node in enumerate(node_list)
                           if not node.abstract]
            to_generate_idx = [i for i, _ in to_generate]
            remaining = len(to_generate)

            if remaining == 0:
                print(f"    所有摘要已存在，跳过生成")
            else:
                print(f"    还需生成 {remaining} 个摘要")

            # 构建提示词
            prompts = []
            for i, node in to_generate:
                ctx = (nodes[node.parent_id].title
                       if node.parent_id and node.parent_id in nodes else "")
                prompt = self._build_abstract_prompt(node.content, node.title, ctx)
                prompts.append(prompt)

            start = time.time()
            done_count = total - remaining

            def progress(done, total_n, last_result):
                print(f"    [{done}/{total_n}] {last_result[:60]}...")

            def checkpoint_callback(buf: list[tuple[int, str]]):
                """每 batch_size 个结果回来时：回填结果并保存 checkpoint"""
                nonlocal done_count
                for idx, result in buf:
                    node_i = to_generate_idx[idx]
                    node_list[node_i].abstract = result or node_list[node_i].content[:200]
                    done_count += 1
                if checkpoint_store and checkpoint_store.forest_dir.exists():
                    checkpoint_store.save(nodes, kb_name="_checkpoint",
                                         save_embeddings=False, save_chroma=False)
                    print(f"    💾 checkpoint @ {done_count}/{total}", flush=True)

            results = pool.generate_batch(
                prompts,
                max_tokens=256,
                show_progress=progress if remaining <= 50 else None,
                batch_size=checkpoint_every,
                batch_callback=checkpoint_callback,
            )

            # 回填剩余未通过 checkpoint 回调处理的结果
            for j, result in enumerate(results):
                node_i = to_generate_idx[j]
                if not node_list[node_i].abstract:
                    node_list[node_i].abstract = result or node_list[node_i].content[:200]

            elapsed = time.time() - start
            print(f"    ✅ 完成！{remaining} 个新摘要，耗时 {elapsed:.1f}s（{remaining/elapsed:.1f}节点/秒）")

        print(f"\n  嵌入向量（{total} 个节点，批量）...")
        embed_start = time.time()

        # 收集需要嵌入的节点（支持断点续传）
        to_embed = [(nid, n) for nid, n in nodes.items() if n.embedding is None]
        if not to_embed:
            print(f"    所有节点已有嵌入，跳过")
        else:
            print(f"    还需嵌入 {len(to_embed)} 个节点")
            BATCH = 32
            for batch_start in range(0, len(to_embed), BATCH):
                batch = to_embed[batch_start:batch_start + BATCH]
                texts = []
                for nid, n in batch:
                    texts.append(f"{n.title}。{n.abstract}" if n.abstract else n.content[:2000])
                try:
                    embs = self._embed_batch(texts)
                    for (nid, n), emb in zip(batch, embs):
                        n.embedding = emb
                except Exception as e:
                    for nid, n in batch:
                        n.embedding = [0.0] * self.DIM
                done = min(batch_start + BATCH, len(to_embed))
                print(f"    {done}/{len(to_embed)}", flush=True)

        print(f"  嵌入完成！耗时 {time.time()-embed_start:.1f}s")

    def _build_abstract_prompt(self, text: str, title: str, context: str) -> str:
        return f"""为以下内容生成一段简洁的语义摘要，概括其核心主题和关键信息。

要求：摘要必须准确反映内容主题，不要添加不存在的信息。控制在80-200字。只输出摘要，不要解释。

{f"[上级主题] {context}" if context else ""}
{f"[节点标题] {title}" if title else ""}
---
[内容]
{text[:3000]}
---
语义摘要："""


# ─── 森林存储 ─────────────────────────────────────
class ForestStore:
    """存储森林结构到磁盘"""

    def __init__(self, kb_path: str):
        self.kb_path = Path(kb_path)
        self.forest_dir = self.kb_path / "forest"
        self.forest_dir.mkdir(parents=True, exist_ok=True)

    def save(self, nodes: dict[str, ForestNode], kb_name: str,
             save_embeddings: bool = True, save_chroma: bool = True,
             embed_api: str = "nvidia", embed_model: str = "",
             embedding_dim: int = 4096):
        from dataclasses import asdict
        import chromadb

        print(f"\n  保存森林到 {self.forest_dir}...")

        # 1. 节点元数据（不含 embedding）
        nodes_meta = {}
        for nid, node in nodes.items():
            d = asdict(node)
            d.pop("embedding", None)
            nodes_meta[nid] = d

        with open(self.forest_dir / "nodes_meta.json", "w", encoding="utf-8") as f:
            json.dump(nodes_meta, f, ensure_ascii=False, indent=2)
        print(f"    节点: {len(nodes_meta)} 条")

        # 2. Embeddings 分片（可选）
        if save_embeddings:
            embeddings = {nid: node.embedding for nid, node in nodes.items() if node.embedding}
            SHARD = 5000
            items = list(embeddings.items())
            for si in range(0, max(len(items), 1), SHARD):
                shard = dict(items[si:si + SHARD])
                with open(self.forest_dir / f"embeddings_{si // SHARD:03d}.json", "w") as f:
                    json.dump(shard, f)
            print(f"    embeddings: {len(embeddings)} 条")
        else:
            print(f"    embeddings: 跳过（checkpoint）")

        # 3. 树结构索引
        tree_index = {nid: nodes[nid].child_ids for nid in nodes}
        with open(self.forest_dir / "tree_index.json", "w", encoding="utf-8") as f:
            json.dump(tree_index, f, ensure_ascii=False)

        # 4. ChromaDB（可选）
        if save_chroma:
            print(f"    存储 ChromaDB...")
            chroma_path = self.kb_path / "chroma_forest"
            chroma_path.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(chroma_path))
            collection = client.get_or_create_collection(name=f"{kb_name}_forest")

            ids, docs, metas, embs = [], [], [], []
            for nid, node in nodes.items():
                if node.embedding is None:
                    continue
                ids.append(nid)
                docs.append(f"{node.title}。{node.abstract}" if node.abstract else node.content[:2000])
                metas.append({
                    "node_id": nid, "title": node.title, "level": node.level,
                    "source": node.source_file, "node_type": node.node_type,
                    "has_children": bool(node.child_ids),
                })
                embs.append(node.embedding)

            BATCH = 500
            for i in range(0, len(ids), BATCH):
                collection.upsert(ids=ids[i:i+BATCH], documents=docs[i:i+BATCH],
                               metadatas=metas[i:i+BATCH], embeddings=embs[i:i+BATCH])
            print(f"    ChromaDB: {len(ids)} 条向量")
        else:
            print(f"    ChromaDB: 跳过（checkpoint）")

        # 5. 元数据
        chroma_path_str = str(self.kb_path / "chroma_forest")
        meta = {
            "kb_name": kb_name, "total_nodes": len(nodes),
            "forest_dir": str(self.forest_dir),
            "chroma_path": chroma_path_str,
            "llm_model": LLM_MODEL,
            "embed_api": embed_api,
            "embed_model": embed_model,
            "embedding_dim": embedding_dim,
            "checkpoint": not save_embeddings,
        }
        with open(self.forest_dir / "forest_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        print(f"  ✅ 保存完成！")


# ─── 森林结构加载器 ─────────────────────────────────
def load_forest_from_json(forest_json_path: str) -> dict[str, ForestNode]:
    """从 LLM 输出的森林 JSON 加载节点

    Args:
        forest_json_path: 森林 JSON 文件路径

    Returns:
        nodes 字典
    """
    with open(forest_json_path, encoding="utf-8") as f:
        data = json.load(f)

    nodes: dict[str, ForestNode] = {}
    for node_data in data.get("nodes", []):
        node = ForestNode(
            node_id=node_data["node_id"],
            title=node_data.get("title", ""),
            level=node_data.get("level", 1),
            content=node_data.get("content", ""),
            abstract=node_data.get("abstract", ""),
            source_file=node_data.get("source_file", ""),
            parent_id=node_data.get("parent_id"),
            child_ids=node_data.get("child_ids", []),
            embedding=None,
            node_type=node_data.get("node_type", "content"),
        )
        nodes[node.node_id] = node

    return nodes


def rebuild_tree_from_relations(nodes: dict[str, ForestNode]):
    """根据 parent_id 重建 child_ids 关系"""
    for node in nodes.values():
        node.child_ids = []

    for node in nodes.values():
        if node.parent_id and node.parent_id in nodes:
            parent = nodes[node.parent_id]
            if node.node_id not in parent.child_ids:
                parent.child_ids.append(node.node_id)


# ─── 构建流程 ─────────────────────────────────────
def build_forest(
    kb_name: str,
    forest_json_path: str,
    generate_abstracts: bool = True,
    llm_workers: int = 8,
    checkpoint_every: int = 16,
    embed_provider: str = "nvidia",
    embed_api_key: str = "",
    embed_model: str = "",
    embed_model_path: str = "",
):
    """构建森林索引

    Args:
        kb_name: 知识库名称
        forest_json_path: LLM 解析输出的 JSON 路径
        generate_abstracts: 是否生成语义摘要
        llm_workers: LLM 并发数
        checkpoint_every: 每多少个节点保存 checkpoint
        embed_provider: 嵌入 provider（nvidia, transformers）
        embed_api_key: API Key（nvidia 用）
        embed_model: 嵌入模型名称
        embed_model_path: 本地模型路径（transformers 用）
    """
    if not forest_json_path:
        raise ValueError("必须提供 --forest-json 参数（LLM 解析输出的 JSON 路径）")

    print(f"\n{'='*60}")
    print(f"🌲 Forest Index Builder")
    print(f"{'='*60}")
    print(f"  知识库: {kb_name}")
    print(f"  森林 JSON: {forest_json_path}")
    print(f"  摘要生成: {'是' if generate_abstracts else '否'}")
    print(f"  LLM 并发: {llm_workers}，checkpoint: 每 {checkpoint_every} 节点")
    print(f"  LLM: {LLM_MODEL} ({LLM_BASE_URL})")
    print(f"  Embedding Provider: {embed_provider}")

    kb_path = str(Path.home() / ".claude" / "knowledge_bases" / kb_name)

    # 加载森林结构（由 LLM 解析输出）
    print(f"\n[Step 1] 从 JSON 加载森林结构...")
    nodes = load_forest_from_json(forest_json_path)
    print(f"  从 {forest_json_path} 加载了 {len(nodes)} 个节点")

    # 统计层级
    level_cnt = {}
    for n in nodes.values():
        level_cnt[n.level] = level_cnt.get(n.level, 0) + 1
    for lvl in sorted(level_cnt):
        print(f"  Level {lvl}: {level_cnt[lvl]} 个节点")

    has_parent = sum(1 for n in nodes.values() if n.parent_id)
    print(f"  有父节点: {has_parent}/{len(nodes)}")

    # 初始化 store（提前创建目录，用于 checkpoint）
    store = ForestStore(kb_path)
    store.forest_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[Step 2] 嵌入 + 语义摘要...")

    # 使用统一的 EmbeddingConfig 创建嵌入模型
    embed_config = {
        "provider": embed_provider,
        "api_key": embed_api_key or os.environ.get("NVIDIA_API_KEY", ""),
        "model": embed_model or ("nvidia/nv-embed-v1" if embed_provider == "nvidia" else ""),
        "model_path": embed_model_path or os.environ.get("RAG_EMBED_MODEL_PATH", ""),
    }
    embed_model_obj = EmbeddingConfig.create_model(embed_config)
    print(f"  嵌入模型: {embed_model_obj.MODEL_NAME} (provider: {embed_model_obj.provider})")

    indexer = ForestIndexer(embed_model_obj)
    indexer.index(
        nodes, generate_abstracts=generate_abstracts,
        llm_workers=llm_workers,
        checkpoint_every=checkpoint_every,
        checkpoint_store=store,
    )

    print(f"\n[Step 3] 存储完整森林（embeddings + ChromaDB）...")
    store.save(
        nodes, kb_name,
        save_embeddings=True, save_chroma=True,
        embed_api=embed_provider,
        embed_model=embed_model_obj.MODEL_NAME,
        embedding_dim=embed_model_obj.DIM,
    )

    print(f"\n{'='*60}")
    print(f"✅ 森林索引构建完成！")
    print(f"   知识库: {kb_name}")
    print(f"   节点总数: {len(nodes)}")
    print(f"   存储: {kb_path}/forest/")
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="构建森林索引（森林结构由 LLM 解析输出为 JSON）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # LLM 解析文档后，加载 JSON 构建森林索引
  python3 forest_builder.py --kb-name my-kb --forest-json ./forest.json

  # 本地 transformers 嵌入
  python3 forest_builder.py --kb-name my-kb --forest-json ./forest.json \\
    --embed-provider transformers --embed-model-path /path/to/model
""",
    )
    parser.add_argument("--kb-name", "-k", required=True, help="知识库名称")
    parser.add_argument("--forest-json", "-f", required=True,
                        help="LLM 解析输出的森林 JSON 路径（必需）")
    parser.add_argument("--no-abstract", action="store_true", help="跳过摘要生成")
    parser.add_argument("--llm-workers", "-w", type=int, default=8,
                        help="LLM 并发数（默认 8）")
    parser.add_argument("--checkpoint-every", "-c", type=int, default=16,
                        help="每多少个节点保存一次 checkpoint（默认 16）")
    parser.add_argument("--embed-provider", default="nvidia",
                        choices=["nvidia", "transformers"],
                        help="嵌入 Provider：nvidia/transformers（默认 nvidia）")
    parser.add_argument("--embed-api-key", default="",
                        help="API Key（nvidia 用，可通过环境变量 NVIDIA_API_KEY 设置）")
    parser.add_argument("--embed-model", default="",
                        help="嵌入模型名称（如 nvidia/nv-embed-v1）")
    parser.add_argument("--embed-model-path", default="",
                        help="本地模型路径（transformers 用）")
    args = parser.parse_args()

    build_forest(
        kb_name=args.kb_name,
        forest_json_path=args.forest_json,
        generate_abstracts=not args.no_abstract,
        llm_workers=args.llm_workers,
        checkpoint_every=args.checkpoint_every,
        embed_provider=args.embed_provider,
        embed_api_key=args.embed_api_key,
        embed_model=args.embed_model,
        embed_model_path=args.embed_model_path,
    )