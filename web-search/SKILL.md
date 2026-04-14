---
name: web-search
description: 通过 inference.sh CLI 进行 Web 搜索和内容提取，支持 Tavily 和 Exa。功能：AI 搜索、内容提取、直接回答、研究。用于：研究、RAG 管道、事实核查、内容聚合、agents。触发词：web search、tavily、exa、search api、content extraction、research、internet search、ai search、search assistant、web scraping、rag。
---

# Web 搜索与提取

通过 [inference.sh](https://inference.sh) CLI 进行 Web 搜索和内容提取。

## 前置条件

需要 inference.sh CLI (`infsh`)。[安装说明](https://raw.githubusercontent.com/inference-sh/skills/refs/heads/main/cli-install.md)

```bash
infsh login
```

## 可用应用

### Tavily

| 应用 | App ID | 说明 |
|------|--------|------|
| Search Assistant | `tavily/search-assistant` | AI 驱动的搜索和回答 |
| Extract | `tavily/extract` | 从 URL 提取内容 |

### Exa

| 应用 | App ID | 说明 |
|------|--------|------|
| Search | `exa/search` | 智能 Web 搜索 |
| Answer | `exa/answer` | 直接的事实回答 |
| Extract | `exa/extract` | 提取和分析 Web 内容 |

## 示例

### Tavily 搜索

```bash
infsh app run tavily/search-assistant --input '{"query": "2024年最新AI发展"}'
```

返回 AI 生成的答案，带来源和图片。

### Tavily 提取

```bash
infsh app run tavily/extract --input '{"urls": ["https://example.com/article1"]}'
```

从多个 URL 提取干净的文本和图片。

### Exa 搜索

```bash
infsh app run exa/search --input '{"query": "机器学习框架对比"}'
```

返回带上下文的高度相关内容链接。

### Exa 回答

```bash
infsh app run exa/answer --input '{"question": "东京的人口是多少？"}'
```

返回直接的事实答案。

## 工作流：研究 + LLM

```bash
# 1. 搜索信息
infsh app run tavily/search-assistant --input '{"query": "量子计算最新进展"}' > search_results.json

# 2. 用 Claude 分析
infsh app run openrouter/claude-sonnet-45 --input '{"prompt": "基于这个研究，总结关键趋势: <search-results>"}'
```

## 工作流：提取 + 总结

```bash
# 1. 从 URL 提取内容
infsh app run tavily/extract --input '{"urls": ["https://example.com/long-article"]}' > content.json

# 2. 用 LLM 总结
infsh app run openrouter/claude-haiku-45 --input '{"prompt": "用3个要点总结这篇文章: <content>"}'
```

## 使用场景

- **研究**: 收集任何主题的信息
- **RAG**: 检索增强生成
- **事实核查**: 用来源验证声明
- **内容聚合**: 从多个来源收集数据
- **Agents**: 构建有研究能力的 AI agents

## 相关资源

```bash
# 全部平台 skill（250+ 应用）
cp -r inference-sh/skills "$HOME/.claude/skills/"

# LLM 模型（结合搜索用于 RAG）
# 结合搜索用于 RAG

# 图片生成
```

浏览所有应用：`infsh app list`

## 文档

- [为 Agents 添加工具](https://inference.sh/docs/agents/adding-tools)
- [构建研究 Agent](https://inference.sh/blog/guides/research-agent)
- [工具集成价值](https://inference.sh/blog/tools/integration-tax)
