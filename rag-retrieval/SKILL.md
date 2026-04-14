---
name: rag-retrieval
description: "RAG（检索增强生成）模式专家。用于构建 RAG 管道、嵌入文档、实现混合搜索、上下文检索、HyDE、Agentic RAG、多模态 RAG、查询分解、重排或 pgvector 搜索。触发词：RAG、检索、LLM、上下文、嵌入、HyDE、重排、pgvector、多模态。"
---

# RAG Retrieval

构建生产级 RAG 系统的综合模式。

## 快速参考

| 类别 | 规则数 | 重要性 | 何时使用 |
|------|---------|--------|----------|
| [Core RAG](#core-rag) | 4 | 关键 | 基础 RAG、引用、混合搜索、上下文管理 |
| [Embeddings](#embeddings) | 3 | 高 | 模型选择、分块、批量/缓存优化 |
| [上下文检索](#上下文检索) | 3 | 高 | 上下文前缀、混合 BM25+vector、管道 |
| [HyDE](#hyde) | 3 | 高 | 词汇不匹配、假想文档生成 |
| [Agentic RAG](#agentic-rag) | 4 | 高 | Self-RAG、CRAG、知识图谱、自适应路由 |
| [多模态 RAG](#多模态-rag) | 3 | 中 | 图文检索、PDF 分块、跨模态搜索 |
| [查询分解](#查询分解) | 3 | 中 | 多概念查询、并行检索、RRF 融合 |
| [重排](#重排) | 3 | 中 | Cross-encoder、LLM 评分、组合信号 |
| [PGVector](#pgvector) | 4 | 高 | PostgreSQL 混合搜索、HNSW 索引、schema 设计 |

**共 30 条规则，9 个类别**

## Core RAG

检索、生成和管道组合的基础模式。

| 规则 | 文件 | 关键模式 |
|------|------|----------|
| 基础 RAG | `rules/core-basic-rag.md` | 检索 + 上下文 + 生成，带引用 |
| 混合搜索 | `rules/core-hybrid-search.md` | RRF 融合（k=60）语义 + 关键词 |
| 上下文管理 | `rules/core-context-management.md` | Token 预算 + 充足性检查 |
| 管道组合 | `rules/core-pipeline-composition.md` | 可组合：分解 → HyDE → 检索 → 重排 |

## Embeddings

嵌入模型、分块策略和生产优化。

| 规则 | 文件 | 关键模式 |
|------|------|----------|
| 模型与 API | `rules/embeddings-models.md` | 模型选择、批量 API、相似度 |
| 分块 | `rules/embeddings-chunking.md` | 语义边界分割，512 token 最佳 |
| 高级 | `rules/embeddings-advanced.md` | Redis 缓存、Matryoshka 维度、批量处理 |

## 上下文检索

Anthropic 的上下文前缀技术 — 减少 67% 检索失败。

| 规则 | 文件 | 关键模式 |
|------|------|----------|
| 上下文前缀 | `rules/contextual-prepend.md` | LLM 生成的上下文 + prompt 缓存 |
| 混合搜索 | `rules/contextual-hybrid.md` | 40% BM25 / 60% vector 权重分割 |
| 完整管道 | `rules/contextual-pipeline.md` | 端到端索引 + 混合检索 |

## HyDE

用于桥接词汇差距的假想文档嵌入。

| 规则 | 文件 | 关键模式 |
|------|------|----------|
| 生成 | `rules/hyde-generation.md` | 嵌入假想文档，而非查询 |
| 每概念 | `rules/hyde-per-concept.md` | 多主题查询的并行 HyDE |
| 回退 | `rules/hyde-fallback.md` | 2-3秒超时 → 直接嵌入回退 |

## Agentic RAG

具有 LLM 驱动决策的自我纠正检索。

| 规则 | 文件 | 关键模式 |
|------|------|----------|
| Self-RAG | `rules/agentic-self-rag.md` | 二进制文档分级相关性 |
| Corrective RAG | `rules/agentic-corrective-rag.md` | CRAG 工作流与网络回退 |
| 知识图谱 | `rules/agentic-knowledge-graph.md` | KG + vector 混合用于实体丰富领域 |
| 自适应检索 | `rules/agentic-adaptive-retrieval.md` | 查询路由到最优策略 |

## 多模态 RAG

图文检索与跨模态搜索。

| 规则 | 文件 | 关键模式 |
|------|------|----------|
| 嵌入 | `rules/multimodal-embeddings.md` | CLIP、SigLIP 2、Voyage multimodal-3 |
| 分块 | `rules/multimodal-chunking.md` | 保留图像的 PDF 提取 |
| 管道 | `rules/multimodal-pipeline.md` | 去重 + 混合检索 + 生成 |

## 查询分解

将复杂查询分解为概念进行并行检索。

| 规则 | 文件 | 关键模式 |
|------|------|----------|
| 检测 | `rules/query-detection.md` | 启发式指标（<1ms 快速路径）|
| 分解 + RRF | `rules/query-decompose.md` | LLM 概念提取 + 并行检索 |
| HyDE 组合 | `rules/query-hyde-combo.md` | 分解 + HyDE 最大覆盖 |

## 重排

检索后重新评分以提高精度。

| 规则 | 文件 | 关键模式 |
|------|------|----------|
| Cross-Encoder | `rules/reranking-cross-encoder.md` | ms-marco-MiniLM（~50ms，免费）|
| LLM 重排 | `rules/reranking-llm.md` | 批量评分 + Cohere API |
| 组合 | `rules/reranking-combined.md` | 多信号加权评分 |

## PGVector

使用 PostgreSQL 的生产级混合搜索。

| 规则 | 文件 | 关键模式 |
|------|------|----------|
| Schema | `rules/pgvector-schema.md` | HNSW 索引 + 预计算 tsvector |
| 混合搜索 | `rules/pgvector-hybrid-search.md` | SQLAlchemy RRF + FULL OUTER JOIN |
| 索引 | `rules/pgvector-indexing.md` | HNSW（快 17 倍）vs IVFFlat |
| 元数据 | `rules/pgvector-metadata.md` | 过滤、boost、Redis 8 比较 |

## 快速开始示例

```python
from openai import OpenAI

client = OpenAI()

async def rag_query(question: str, top_k: int = 5) -> dict:
    """带引用的基础 RAG。"""
    docs = await vector_db.search(question, limit=top_k)
    context = "\n\n".join([f"[{i+1}] {doc.text}" for i, doc in enumerate(docs)])

    response = await llm.chat([
        {"role": "system", "content": "用内联引用 [1], [2] 回答。仅使用提供的上下文。"},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ])

    return {"answer": response.content, "sources": [d.metadata['source'] for d in docs]}
```

## 关键决策

| 决策 | 建议 |
|------|------|
| 嵌入模型 | `text-embedding-3-small`（通用），`voyage-3`（生产）|
| 分块大小 | 256-1024 token（通常 512）|
| 混合权重 | 40% BM25 / 60% vector |
| Top-k | 3-10 个文档 |
| Temperature | 0.1-0.3（factual）|
| 上下文预算 | 4K-8K token |
| 重排 | 检索 50，重排到 10 |
| 向量索引 | HNSW（生产），IVFFlat（高容量）|
| HyDE 超时 | 2-3 秒，带回退 |
| 查询分解 | 启发式优先，多概念才用 LLM |

## 常见错误

1. 无引用跟踪（无法验证的答案）
2. 上下文太大（稀释相关性）
3. 单一检索方法（错过关键词匹配）
4. 长文档未分块（上下文丢失）
5. 查询和文档嵌入方式不同
6. Agentic RAG 无回退路径（工作流卡住）
7. 无限重写循环（无重试限制）
8. 使用错误的相似度指标（cosine vs euclidean）
9. 未缓存嵌入（重复计算不变内容）
10. 多模态 RAG 缺少图像标题（限制文本搜索）
