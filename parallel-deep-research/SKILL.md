---
name: parallel-deep-research
description: "深度研究工具。仅在用户明确说'深度研究'、'深入调查'、'全面报告'时使用。比普通搜索慢 10-100 倍。对于普通研究/查找请求，使用 parallel-web-search。支持多轮：传递 --previous-interaction-id 以继续之前的上下文。"
---

# Deep Research

深度研究工具，用于深入调查主题。

## 何时使用（vs parallel-web-search）

**仅在用户明确请求深度/彻底研究时使用此 skill。** 深度研究比 parallel-web-search 慢 10-100 倍。对于普通"研究 X"请求、快速查找或事实核查，使用 **parallel-web-search**。

## Step 1: 启动研究

```bash
parallel-cli research run "$ARGUMENTS" --processor pro-fast --no-wait --json
```

如果是**跟进**之前的研究或 enrichment 任务，知道 `interaction_id`，添加上下文链接：

```bash
parallel-cli research run "$ARGUMENTS" --processor lite --no-wait --json --previous-interaction-id "$INTERACTION_ID"
```

通过在请求间链接 `interaction_id`，每个后续问题自动具有之前轮次的完整上下文。后续使用 `--processor lite` 因为重型研究已在初始轮次完成。

此命令立即返回。**必须使用 `--no-wait`** — 否则命令会阻塞数分钟并超时。

处理器选项（根据用户请求选择）：

| 处理器 | 预期延迟 | 使用场景 |
|--------|----------|----------|
| `pro-fast` | 30秒 – 5分钟 | 默认 — 深度和速度的良好平衡 |
| `ultra-fast` | 1 – 10分钟 | 更深入分析，更多来源（~2倍成本）|
| `ultra` | 5 – 25分钟 | 最大深度，仅在明确请求时使用（~3倍成本）|

解析 JSON 输出，提取 `run_id`、`interaction_id` 和监控 URL。立即告知用户：
- 深度研究已启动
- 所选处理器层的预期延迟（见上表）
- 监控 URL（用于跟踪进度）

## Step 2: 轮询结果

选择基于主题的描述性文件名（例如 `ai-chip-market-2026`、`react-vs-vue-comparison`）。使用小写和连字符，无空格。

```bash
parallel-cli research poll "$RUN_ID" -o "$FILENAME" --timeout 540
```

重要：
- 使用 `--timeout 540`（9 分钟）以保持在工具执行限制内
- 不要传递 `--json` — 完整输出很大，会淹没上下文。`-o` 标志将结果写入文件
- `-o` 标志生成两个输出文件：
  - `$FILENAME.json` — 元数据和依据
  - `$FILENAME.md` — 格式化的 markdown 报告
- 轮询命令在研究完成时打印**执行摘要**到 stdout。与用户分享此执行摘要。

### 如果轮询超时

更高的处理器层可能需要超过 9 分钟。如果轮询退出但未完成：
1. 告知用户研究仍在服务器端运行
2. 重新运行相同的 `parallel-cli research poll` 命令继续等待

## 响应格式

**Step 1 后：** 分享监控 URL（仅用于跟踪进度 — 不是最终报告）。

**Step 2 后：**
1. 分享轮询命令打印到 stdout 的**执行摘要**
2. 告知用户两个生成的文件路径：
   - `$FILENAME.md` — 格式化的 markdown 报告
   - `$FILENAME.json` — 元数据和依据
3. 分享 `interaction_id` 并告知用户可以提出后续问题（"深入 X" 或 "与 Y 对比"）

完成后不要再分享监控 URL — 结果在文件中。

询问用户是否想阅读文件获取更多详情。除非用户要求，否则不要将文件内容读入上下文。

**记住 `interaction_id`** — 如果用户提出与此研究相关的后续问题，将其用作下一个研究或 enrichment 命令的 `--previous-interaction-id`。

## 安装

如果找不到 `parallel-cli`，安装并认证：

```bash
curl -fsSL https://parallel.ai/install.sh | bash
```

如果无法以这种方式安装，通过 pipx 安装：

```bash
pipx install "parallel-web-tools[cli]"
pipx ensurepath
```

然后认证：

```bash
parallel-cli login
```

或设置 API 密钥：`export PARALLEL_API_KEY="your-key"`
