# Advanced RAG 研究：森林索引 + DeepSearch 检索

> 研究日期：2026-04-06
> 参考：KohakuRAG、FABLE、RAPTOR、Bridge-RAG、HiSem-RAG、HERB Benchmark

---

## 一、当前 RAG 的瓶颈

传统 flat chunking RAG 的问题：

| 问题 | 说明 |
|------|------|
| **结构丢失** | 按固定大小/段落切分，破坏原始文档结构，无法追踪引用来源 |
| **词汇鸿沟** | 用户问题和文档用语不同（如 "PUE" vs "power usage effectiveness"）导致检索失败 |
| **语义噪声** | 向量相似度匹配只做表面语义，不深究答案相关性 |
| **单次检索** | 一次 query 返回结果，无法处理复杂多跳问题 |
| **Lost in the Middle** | 长上下文 LLM 会遗漏中间位置的信息 |

---

## 二、范式一：森林索引（Knowledge Forest / Tree-based Indexing）

### 核心思想

将文档解析为**多层语义树**（Forest = 多棵树的集合），每个节点都有独立的语义表示。检索时可以「放大看细节」或「缩小看全貌」。

### 代表工作

#### 2.1 KohakuRAG（2025，ICLR 评分第 1）

**四层树结构**：Document → Section → Paragraph → Sentence

```
Document（文档）
  └── Section（章节，如 "第3章 魔法"）
        └── Paragraph（段落）
              └── Sentence（句子）
```

**构建方式**：
1. 解析文档结构（TOC → 标题层级）
2. 句子级嵌入 → 向上聚合为段落 → 章节 → 文档
3. 聚合方式：长度加权平均（length-weighted aggregation）

**检索特点**：
- **Multi-Query**：LLM 将用户问题扩展为多个不同表述的查询，覆盖同义词/不同角度
- **Cross-Query Reranking**：被更多查询命中的节点排名更高（共识信号）
- **Ensemble Inference**：多次推理 + 投票，过滤空白回答

**效果**：WattBot 2025 挑战赛第一名（分数 0.861），精确到 ±0.1% 的数值答案 + 精确引用

---

#### 2.2 FABLE（2025，ACL）

**Forest-based Adaptive Bi-Path LLM-Enhanced Retrieval**

- **Forest 索引**：每个文档构建多粒度语义层次结构（LLM 参与增强）
- **Bi-Path 检索**：
  - **Path 1**：LLM 引导的层级遍历（LLM 决定「放大」还是「缩小」）
  - **Path 2**：结构感知传播（structure-aware propagation）
- **自适应效率控制**：显式 budget control，token 减少 94% 但精度相当

---

#### 2.3 RAPTOR（2024）

**Recursive Abstractive Processing for Tree-Organized Retrieval**

- **递归聚类 + 摘要**：将叶子 chunks 聚类 → LLM 生成摘要作为父节点 → 递归向上
- **双重粒度**：根节点提供全局视野，叶子节点提供细节
- **RAPTOR retrieval**：在推理时从树中整合不同抽象层级的信息
- 已集成到 RAGFlow（`enable_raptor`）

---

#### 2.4 Bridge-RAG（2025，北大）

**Abstract Bridge Tree + Cuckoo Filter**

- **核心创新**：引入 **Abstract（抽象节点）** 作为 query entity 和 document chunk 之间的桥梁
- **分层抽象树**：
  - 实体（Entity）→ Abstract（桥接）→ Document Chunk
  - 支持从实体到 chunk 的多级上下文检索
- **Cuckoo Filter**：O(1) 实体查找，提升效率 10×~500×
- 精度提升 15.65%

---

#### 2.5 HiSem-RAG（2025）

**Hierarchical Semantic-Driven RAG**

- **分层语义索引**：保留段落边界和语义完整性
- **Distribution-aware Adaptive Threshold**：动态调整检索范围
- **双向语义增强**：通过标题路径（title path）和知识点摘要（knowledge point summary）传递上下文

---

### 总结：森林索引的核心机制

```
构建阶段：
  文档 → TOC 解析 → 树结构
                  ↓
          LLM 生成摘要/抽象节点（可选）
                  ↓
          自底向上嵌入聚合（叶子→根）
                  ↓
          多粒度向量节点存入 Vector DB

检索阶段：
  用户问题 → 扩展多查询 / LLM 规划
                  ↓
          层级遍历（从根/高抽象层开始，逐层聚焦）
                  ↓
          汇聚多粒度上下文（广度 + 深度）
                  ↓
          LLM 生成答案
```

---

## 三、范式二：DeepSearch 检索

### 核心思想

DeepSearch 不是简单的「检索 → 生成」，而是一种需要**多跳推理、跨源追溯、迭代细化**的复杂检索范式。

### 与传统 RAG 的区别

| 维度 | 传统 RAG | DeepSearch |
|------|---------|-----------|
| 查询 | 单次 query | 分解为多步子查询 |
| 推理 | 单跳 | 多跳（multi-hop）|
| 数据源 | 单文档/集合 | 异构（文档、Slack、会议记录、GitHub 等）|
| 上下文 | 相似 chunks | 跨源关联推理 |
| 适用场景 | 事实问答 | 复杂分析、竞争分析、归因 |

### HERB Benchmark（Salesforce 2025）

**HERB = Heterogeneous Enterprise RAG Benchmark**

- 39190 个企业 artifacts（文档、会议、Slack、GitHub、URL）
- 多跳问题示例：
  > "搜索 Slack 中关于竞品名称的讨论 → 对每个竞品，再次搜索 Slack 提取共享的 demo URL"

**关键发现**：
- 即使最佳 agentic RAG 方法平均得分仅 **32.96/100**
- **Retrieval 是主要瓶颈**：现有方法无法进行深度搜索和检索所有必要证据
- 常在部分上下文中推理，导致显著性能下降

### DeepSearch 的关键能力

1. **Query Decomposition**：将复杂问题分解为多个子查询
2. **Source Navigation**：知道去哪里找（跨源）
3. **Iterative Refinement**：第一跳结果触发第二跳查询
4. **Cross-source Synthesis**：合并异构来源的上下文

---

## 四、两者结合：森林 + DeepSearch

用户描述的正是这两种范式的融合：

### 阶段一：森林索引构建

```
1. 编译目录结构（TOC）
      ↓
2. 将 md 文件解析为树
      ↓
3. 每个节点：
      - 语义嵌入（使用 LLM 生成摘要/抽象描述）
      - 父子关系（继承上下文）
      - 元数据（来源文件、层级、关键词）
      ↓
4. 存储为 Forest 结构
      - 树节点表（node_id, parent_id, content, embedding, level, metadata）
      - 向量索引（每个节点的 embedding）
```

### 阶段二：DeepSearch 检索

```
1. Query 分解：LLM 将用户问题分解为多个子查询
      ↓
2. 森林遍历：
      - 从根节点（高层摘要）开始
      - 评估每个子查询与节点的语义匹配
      - 向下「聚焦」（zoom in）到相关分支
      - 跨分支收集相关节点
      ↓
3. 多跳检索：
      - 第一跳：找到最相关的子树/节点
      - 第二跳：根据已找到的节点，探索邻居节点/兄弟节点
      - 收集足够上下文后停止
      ↓
4. 答案生成：基于汇聚的多粒度上下文生成答案
```

---

## 五、对我们现有 RAG 系统的改进建议

### 当前系统（基于 ChromaDB flat chunking）

```
文档 → 分块（chunk_size=500）→ 嵌入 → ChromaDB
查询 → 嵌入 → Top-K 相似 → 生成
```

### 目标系统（Forest + DeepSearch）

```
【构建阶段】
1. 解析 md 的 TOC/标题结构 → 建立父子关系
2. 按节点级别生成语义描述（LLM 生成 abstract/summary）
3. 自底向上聚合嵌入（如：叶子取平均 → 父节点）
4. 存储：节点表 + 层级 + ChromaDB 向量

【检索阶段】
1. LLM 分解用户问题 → 多个子查询
2. 森林遍历：
   - 高层节点（抽象/摘要）快速判断相关子树
   - 低层节点（细节）获取精确答案
   - distance 阈值动态调整
3. 多跳：相关节点 → 探索其兄弟/父子节点
4. 汇聚上下文 → 生成答案
```

### 实施优先级

| 优先级 | 改进 | 工作量 | 效果 |
|--------|------|--------|------|
| 🔴 P0 | Tree Indexing（TOC 解析 + 多层节点）| 高 | 引用精确、结构保留 |
| 🟡 P1 | Multi-Query Expansion（LLM 扩展查询）| 中 | 解决词汇鸿沟 |
| 🟡 P1 | Query Decomposition（DeepSearch 多跳）| 高 | 复杂问题支持 |
| 🟢 P2 | Abstract/Summary 节点生成 | 高 | 提升抽象层检索 |
| 🟢 P2 | Bi-Path 检索（FABLE 风格）| 高 | 自适应精度/效率 |

---

## 六、参考论文

- **KohakuRAG** (2025) - arXiv:2603.07612 - ICLR 2025 评分第一
- **FABLE** (2025) - arXiv:2601.18116 - ACL 2025 - Forest + Bi-Path
- **RAPTOR** (2024) - ICLR - 递归摘要树
- **Bridge-RAG** (2025) - arXiv:2603.26668 - 抽象桥接树 + Cuckoo Filter
- **HiSem-RAG** (2025) - MDPI Applied Sciences - 分层语义驱动
- **HERB Benchmark** (2025) - arXiv:2506.23139 - DeepSearch 标准
- **RAGFlow 2025 Review** - RAGFlow 官方博客
