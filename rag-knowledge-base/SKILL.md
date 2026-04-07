---
name: rag-knowledge-base
description: RAG 本地知识库管理 Skill。功能：① 从任意格式文档构建向量知识库（支持扁平分块和森林索引）；② 作为 AI 助手的知识检索后端，支持向量化检索和上下文问答。支持联网嵌入（NVIDIA NIM）和本地嵌入（Transformers）。触发词：知识库、RAG、向量知识库、构建知识库、基于文档问答。
---

# RAG 知识库 Skill

将任意格式的文档集合构建为向量知识库，并作为 AI 助手的检索后端。

## 架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            模块化 RAG 系统                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────┐    ┌─────────────┐    ┌─────────────────┐       │
│  │ query_rewrite.py│───▶│embeddings.py│───▶│forest_retriever.py│       │
│  │                 │    │             │    │                  │       │
│  │  查询扩展/分解   │    │  嵌入模型   │    │  森林结构检索    │       │
│  └────────┬────────┘    └─────────────┘    └────────┬─────────┘       │
│           │                                        │                  │
│           └────────────────┬───────────────────────┘                  │
│                            │                                          │
│                            ▼                                          │
│                  ┌─────────────────────┐                            │
│                  │  deep_searcher.py   │                            │
│                  │   多跳深度检索      │                            │
│                  └──────────┬──────────┘                            │
│                             │                                         │
│                             ▼                                         │
│                  ┌─────────────────────┐                            │
│                  │      ChromaDB       │                            │
│                  │ ~/.claude/knowledge_ │                            │
│                  │     bases/<kb>/      │                            │
│                  └─────────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 首次使用配置

首次调用此 Skill 时，需要询问用户以下配置：

### 1. 嵌入模型配置

| 问题 | 选项 | 说明 |
|------|------|------|
| 嵌入模型使用方式 | 联网 / 本地 | 联网使用 API，本地使用本地模型 |
| 如果选择联网 | API 类型 | NVIDIA NIM（推荐）|
| | API 地址 | `https://integrate.api.nvidia.com/v1/embeddings` |
| | API Key | NVIDIA API Key |
| | 模型名称 | `nvidia/nv-embed-v1`、`nvidia/llama-nemotron-embed-1b-v2`、`baai/bge-m3` |
| 如果选择本地 | 模型路径 | 本地模型文件夹路径 |
| | 模型维度 | 如 1024、4096 |

### 2. LLM 配置（仅构建森林索引时需要）

| 问题 | 选项 | 说明 |
|------|------|------|
| LLM 使用方式 | 联网 / 本地 | 联网使用 API，本地使用本地模型 |
| API 地址 | | LLM API 端点 |
| API Key | | 对应 API 的密钥 |
| 模型名称 | | 如 `gpt-4o-mini`、`qwen2.5:7b` |

### 配置优先级

1. 显式参数（命令行） > 环境变量 > 默认值
2. 环境变量：
   - `NVIDIA_API_KEY`：NVIDIA API Key
   - `RAG_EMBED_PROVIDER`：嵌入 provider（nvidia/transformers）
   - `RAG_EMBED_MODEL`：嵌入模型名称
   - `RAG_EMBED_MODEL_PATH`：本地嵌入模型路径
   - `RAG_EMBED_DIM`：嵌入维度

---

## Part 1：构建知识库（工具模式）

### 安装依赖

```bash
pip install langchain langchain-chroma chromadb requests langchain-text-splitters transformers torch
```

### 快速开始

```bash
# 联网嵌入（NVIDIA NIM）
export NVIDIA_API_KEY=your_key_from_build_nvidia_com
python3 scripts/rag_kb.py build --name my-kb --input ./docs

# 本地 transformers 嵌入
export RAG_EMBED_MODEL_PATH=/path/to/your/model
python3 scripts/rag_kb.py build --name my-kb --input ./docs --embed-provider transformers
```

### 构建参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--name` | 必需 | 知识库名称 |
| `--input` | 必需 | md 文件或目录 |
| `--embed-provider` | `nvidia` | `nvidia`（联网）/ `transformers`（本地）|
| `--embed-model` | `nvidia/nv-embed-v1` | 嵌入模型 |
| `--chunk-size` | `500` | 分块大小（字符） |
| `--chunk-overlap` | `50` | 分块重叠 |

### 管理命令

```bash
python3 scripts/rag_kb.py list                              # 列出所有知识库
python3 scripts/rag_kb.py manage --name my-kb --action stats  # 查看统计
python3 scripts/rag_kb.py manage --name my-kb --action add --input ./new_docs  # 增量添加
python3 scripts/rag_kb.py manage --name my-kb --action remove # 删除知识库
```

---

## Part 2：森林索引（高级）

森林索引是一种**层次化语义索引**结构，每个节点包含：
- `node_id`：唯一标识
- `title`：标题
- `level`：层级深度
- `content`：原始内容
- `abstract`：LLM 生成的语义摘要
- `parent_id` / `child_ids`：树结构关系

### 核心理念：解析器与索引器分离

```
                    ┌─────────────────────────┐
                    │    解析器 (Parser)       │
                    │  LLM 实现，适配任意格式   │
                    └───────────┬─────────────┘
                                │
                    森林结构 JSON (Forest JSON)
                                │
                    ┌───────────▼─────────────┐
                    │   森林索引器 (Indexer)   │
                    │   Python 调用，只负责     │
                    │   摘要生成 + 向量化      │
                    └─────────────────────────┘
```

**解析器由 LLM 实现**，可以解析任意格式：
- Markdown（按标题层级）
- PDF（按章节）
- HTML（按标签结构）
- JSON（按字段嵌套）
- 表格（按行列关系）
- 自定义格式

**索引器是通用的**，只负责：
1. 读取森林结构 JSON
2. 生成语义摘要（LLM）
3. 向量化并存储

### 森林结构 JSON 格式

LLM 解析后输出标准格式：

```json
{
  "nodes": [
    {
      "node_id": "doc1/chapter1/section1",
      "title": "第一节",
      "level": 3,
      "content": "章节内容...",
      "abstract": "",
      "source_file": "doc1.md",
      "parent_id": "doc1/chapter1",
      "child_ids": [],
      "node_type": "section"
    }
  ]
}
```

### 构建森林索引

#### Step 1：LLM 解析文档，输出森林 JSON

让 LLM 解析你的文档，输出森林结构 JSON（格式见下方）。

#### Step 2：调用索引器构建

```bash
#联网嵌入
python3 scripts/forest_builder.py \
  --kb-name my-kb \
  --forest-json ./forest.json \
  --embed-provider nvidia

# 本地 transformers 嵌入
python3 scripts/forest_builder.py \
  --kb-name my-kb \
  --forest-json ./forest.json \
  --embed-provider transformers \
  --embed-model-path /path/to/model
```

### 森林索引参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--kb-name` | 必需 | 知识库名称 |
| `--forest-json` | 必需 | LLM 解析输出的森林 JSON 路径 |
| `--embed-provider` | `nvidia` | 嵌入 provider |
| `--embed-api-key` | 环境变量 | API Key |
| `--embed-model` | | 嵌入模型名称 |
| `--embed-model-path` | | 本地模型路径 |
| `--no-abstract` | False | 跳过摘要生成 |
| `--llm-workers` | `8` | LLM 并发数 |
| `--checkpoint-every` | `16` | 每多少节点保存 checkpoint |

### LLM 解析器示例提示词

让 LLM 输出森林 JSON 时，可使用类似提示词：

```
请解析以下文档，构建语义森林结构。

要求：
1. 每个标题/章节作为一个节点
2. 记录 node_id、title、level、content
3. 建立父子关系（parent_id、child_ids）
4. 只输出 JSON，不要解释
5. content 字段只包含该节点下的直接内容，不含子节点内容

输出格式：
{
  "nodes": [
    {"node_id": "...", "title": "...", "level": 1, "content": "...", "parent_id": null, ...}
  ]
}
```

---

## Part 3：AI 助手集成（助手模式）

当 AI 助手需要回答用户关于某个知识库的问题时，使用 `scripts/query_kb.py` 检索相关片段，再结合自身知识回答。

### 检索流程

```
用户问题
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Query Rewrite (可选)                              │
│  ┌──────────────┐  ┌─────────────────┐                    │
│  │ Query Expansion│  │Query Decomposition│                    │
│  │ 同义词扩展   │  │ 分解为子问题    │                    │
│  └──────────────┘  └─────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: Forest Retriever                                │
│  ┌──────────────┐  ┌─────────────────┐                    │
│  │Top-Down     │  │Parent Traversal │                    │
│  │从根向下聚焦   │  │收集祖先节点    │                    │
│  └──────────────┘  └─────────────────┘                    │
│  ┌──────────────┐  ┌─────────────────┐                    │
│  │Siblings     │  │Subtree          │                    │
│  │兄弟节点扩展  │  │子树聚合        │                    │
│  └──────────────┘  └─────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: Deep Searcher (可选)                             │
│                                                              │
│  Hop 1 ──▶ 触发查询 ──▶ Hop 2 ──▶ 收敛停止                │
│                                                              │
│  根据当前结果判断是否需要继续检索                           │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
  Top-K 结果
```

### 检索调用

```bash
# 基础检索
python3 scripts/query_kb.py --kb-name my-kb --query "问题" --top-k 5

# 启用查询扩展（生成同义词变体）
python3 scripts/query_kb.py --kb-name my-kb --query "问题" --expand

# 启用查询分解（复杂问题拆分为子问题）
python3 scripts/query_kb.py --kb-name my-kb --query "复杂问题" --decompose

# 启用多跳深度检索
python3 scripts/query_kb.py --kb-name my-kb --query "问题" --deep-search

# 综合启用
python3 scripts/query_kb.py --kb-name my-kb --query "问题" --expand --decompose --deep-search --verbose
```

### 检索参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--top-k` | `5` | 返回结果数 |
| `--expand` | `False` | 启用查询扩展 |
| `--decompose` | `False` | 启用查询分解 |
| `--deep-search` | `False` | 启用多跳深度检索 |
| `--max-hops` | `3` | 最大跳数 |
| `--no-parent` | `False` | 禁用父节点遍历 |
| `--siblings` | `False` | 启用兄弟节点扩展 |
| `--subtree` | `False` | 启用子树聚合 |
| `--depth` | `3` | Top-Down 遍历深度 |
| `--verbose` | `False` | 显示详细信息 |

### 助手回答格式

```
📖 来源：玩家手册/魔法/法术详述/3环.md

[基于检索内容的回答，简洁准确]
```

### 回答规则

- ✅ 检索到相关内容 → 基于内容回答，注明来源
- ⚠️ 检索弱相关（距离 > 0.8）→ 补充自身知识，说明
- ❌ 无相关检索 → 明确告知不知道，不编造

---

## 知识库信息

| 项目 | 值 |
|------|-----|
| 存储路径 | `~/.claude/knowledge_bases/<kb_name>/` |
| 向量数据库 | `chroma/`（扁平）、`chroma_forest/`（森林） |
| 元数据 | `metadata.json`、`forest/forest_meta.json` |
| 嵌入模型（默认） | `nvidia/nv-embed-v1`（4096 维） |
| API | NVIDIA NIM（联网） |

---

## 已有知识库

| 名称 | 片段数 | 嵌入模型 | 来源 |
|------|--------|---------|------|
| `dnd` | 31273 | nvidia/nv-embed-v1 | DND v2026.02.12 规则书 |

---

## 脚本架构

```
scripts/
├── llm.py                 # LLM 统一接口
│                            #   - generate_text() 单次调用
│                            #   - LLMThreadPool 批量并发调用
│                            #   - generate_abstract() 摘要生成
│                            #   - generate_query_expansions() 查询扩展
│                            #   - generate_query_decomposition() 查询分解
├── embeddings.py            # 嵌入模型统一接口
│                            #   - requests 框架：NvidiaEmbeddings
│                            #   - transformers 框架：TransformersEmbeddings
│                            #   - EmbeddingConfig 配置管理器
├── forest_builder.py       # 森林索引构建（调用 llm + embeddings）
├── query_rewrite.py         # 查询改写模块
│                            #   - expand_query() 同义词扩展
│                            #   - decompose_query() 分解为子问题
│                            #   - transform_query() 综合转换
├── forest_retriever.py      # 森林检索器
│                            #   - ForestRetriever 检索器类
│                            #   - top_down_traverse() Top-Down 遍历
│                            #   - parent_traversal() 父节点遍历
│                            #   - siblings_expansion() 兄弟节点扩展
│                            #   - subtree_aggregation() 子树聚合
├── deep_searcher.py         # 多跳深度检索器
│                            #   - DeepSearcher 多跳搜索类
│                            #   - multi_hop_search() 多跳检索
│                            #   - generate_hop_trigger() 生成触发查询
├── query_kb.py              # 主检索入口（整合所有模块）
├── query.py                 # 带 LLM 生成的查询
├── manage.py                # 管理工具
└── rag_kb.py               # 统一 CLI
```

---

## 嵌入模型支持

| Provider | 框架 | 说明 |
|----------|------|------|
| `nvidia` | requests | NVIDIA NIM API，需要 API Key |
| `transformers` | transformers | 本地 transformers 模型，支持 MPS GPU |

---

## 环境变量

| 变量 | 说明 |
|------|------|
| `NVIDIA_API_KEY` | NVIDIA NIM API Key（嵌入用） |
| `LLM_API_KEY` | LLM API Key（摘要生成用） |
| `LLM_MODEL` | LLM 模型名称（默认 gpt-4o-mini） |
| `LLM_BASE_URL` | LLM API 端点 |
| `RAG_EMBED_PROVIDER` | 嵌入 provider |
| `RAG_EMBED_MODEL` | 嵌入模型名称 |
| `RAG_EMBED_MODEL_PATH` | 本地嵌入模型路径 |
| `RAG_EMBED_DIM` | 嵌入向量维度 |
| `RAG_EMBED_BASE_URL` | API 端点地址 |