# RAG 原理详解

## 什么是 RAG

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合信息检索与文本生成的技术。核心思想：让大模型在回答问题前，先从外部知识库检索相关信息，再基于检索结果生成答案。

**解决的问题：**
- 大模型知识过时、幻觉
- 无法访问私有/实时数据
- 通用模型在垂直领域精度不足

## RAG 发展三阶段

### 1. 朴素 RAG（Naive RAG）
全文检索或向量检索 → 直接返回结果。缺点：缺乏语义理解能力，检索精度有限。

### 2. 进阶 RAG（Advanced RAG）
在 Naive RAG 基础上优化检索前/中/后三阶段：
- **检索前**：Query 重写、Embedding 微调
- **检索中**：混合检索（向量 + 关键词）
- **检索后**：Rerank 重排序，筛选最相关片段

### 3. 智能体 RAG（Agentic RAG）
多 Agent 协作，动态决策检索策略，实时调用外部工具，高级场景应用。

## 知识库构建流程

### 数据准备
- **文档格式**：Markdown（推荐）、PDF、TXT、Word
- **命名规范**：简洁、有意义、避免特殊字符
- **内容规范**：清晰层级标题，图片/表格独立处理

### 文本分块（Chunking）
```
chunk_size = 500       # 每块字符数
chunk_overlap = 50     # 块间重叠字符（保持上下文连贯）
```
- 过小：丢失上下文，检索碎片化
- 过大：引入噪声，降低检索精度
- 重叠：保证块间语义连续

### 向量化（Embedding）
```python
from langchain_ollama import OllamaEmbeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vector = embeddings.embed_query("文本内容")
```
模型选择：
- `nomic-embed-text`：多语言支持，推荐中文场景
- `bge-large-zh-v1.5`：中文专用，高精度

### 向量数据库
```python
from langchain_chroma import Chroma
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="my-kb",
)
vectorstore.add_documents(chunks)
```
ChromaDB 是本地轻量向量库，数据存储在 `~/.claude/knowledge_bases/<kb_name>/chroma/`。

## 检索与生成

### 检索阶段
```python
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
results = retriever.invoke("用户问题")
```
- `k`：返回 Top-K 个最相似片段
- 相似度：余弦相似度（Cosine Similarity）
- 混合检索：向量检索 + BM25 关键词检索结合

### Prompt 组装
```
参考材料：
[1] 来源: file1.md
    内容摘要...

[2] 来源: file2.md
    内容摘要...

用户问题：XX 是什么？
```
将多个片段组装进 Prompt，确保 LLM 看到完整上下文。

### LLM 生成
```python
llm = ChatOllama(model="qwen2.5:7b", temperature=0.3)
response = llm.invoke(formatted_prompt)
```
- `temperature=0`：精确回答，减少幻觉
- `temperature=0.7-1.0`：创造性回答

## 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 检索结果为空 | Embedding 模型未启动 | `ollama pull nomic-embed-text` |
| LLM 回答不准确 | 检索片段不相关 | 增大 chunk_size，调整 top_k |
| 回答幻觉 | 检索内容不足以回答 | 降低 temperature，或告知无法回答 |
| 构建速度慢 | 文档过多 | 减少 chunk_size，减少 Ollama 调用 |
