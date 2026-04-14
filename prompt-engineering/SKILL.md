---
name: prompt-engineering
description: "AI 模型提示工程指南：LLM、图像生成器、视频模型。技术：思维链、少样本、系统提示、负提示。模型：Claude、GPT-4、Gemini、FLUX、Veo、Stable Diffusion 提示。用于：更好的 AI 输出、一致的结果、复杂任务、优化。触发词：提示工程、如何提示、更好的提示、提示技巧、提示指南、LLM 提示、图像提示、AI 提示、提示优化、提示模板、提示结构、有效提示、提示技术。"
---

# Prompt Engineering Guide

通过 [inference.sh](https://inference.sh) CLI 学习 AI 模型的提示工程。

## 快速开始

> 需要 inference.sh CLI (`infsh`)。[安装说明](https://raw.githubusercontent.com/inference-sh/skills/refs/heads/main/cli-install.md)

```bash
infsh login
```

## LLM 提示

### 基本结构

```
[角色/上下文] + [任务] + [约束] + [输出格式]
```

### 角色提示

```bash
infsh app run openrouter/claude-sonnet-45 --input '{
  "prompt": "You are an expert data scientist with 15 years of experience in machine learning. Explain gradient descent to a beginner, using simple analogies."
}'
```

### 任务清晰度

```bash
# 差：模糊
"Help me with my code"

# 好：具体
"Debug this Python function that should return the sum of even numbers from a list, but returns 0 for all inputs:

def sum_evens(numbers):
    total = 0
    for n in numbers:
        if n % 2 == 0:
            total += n
        return total

Identify the bug and provide the corrected code."
```

### 思维链（Chain-of-Thought）

```bash
infsh app run openrouter/claude-sonnet-45 --input '{
  "prompt": "Solve this step by step:\n\nA store sells apples for $2 each and oranges for $3 each. If someone buys 5 fruits and spends $12, how many of each fruit did they buy?\n\nThink through this step by step before giving the final answer."
}'
```

### 少样本示例（Few-Shot）

```bash
infsh app run openrouter/claude-sonnet-45 --input '{
  "prompt": "Convert these sentences to formal business English:\n\nExample 1:\nInput: gonna send u the report tmrw\nOutput: I will send you the report tomorrow.\n\nExample 2:\nInput: cant make the meeting, something came up\nOutput: I apologize, but I will be unable to attend the meeting due to an unforeseen circumstance.\n\nNow convert:\nInput: hey can we push the deadline back a bit?"
}'
```

### 输出格式规范

```bash
infsh app run openrouter/claude-sonnet-45 --input '{
  "prompt": "Analyze the sentiment of these customer reviews. Return a JSON array with objects containing \"text\", \"sentiment\" (positive/negative/neutral), and \"confidence\" (0-1).\n\nReviews:\n1. \"Great product, fast shipping!\"\n2. \"Meh, its okay I guess\"\n3. \"Worst purchase ever, total waste of money\"\n\nReturn only valid JSON, no explanation."
}'
```

### 约束设置

```bash
infsh app run openrouter/claude-sonnet-45 --input '{
  "prompt": "Summarize this article in exactly 3 bullet points. Each bullet must be under 20 words. Focus only on actionable insights, not background information.\n\n[article text]"
}'
```

## 图像生成提示

### 基本结构

```
[主体] + [风格] + [构图] + [光线] + [技术参数]
```

### 质量关键词

```
photorealistic, 8K, ultra detailed, sharp focus, professional,
masterpiece, high quality, best quality, intricate details
```

## 高级技术

### 系统提示

```bash
infsh app run openrouter/claude-sonnet-45 --input '{
  "system": "You are a helpful coding assistant. Always provide code with comments. If you are unsure about something, say so rather than guessing.",
  "prompt": "Write a Python function to validate email addresses using regex."
}'
```

### 迭代优化

```bash
# 从宽泛开始
# 添加具体细节
# 添加风格
# 添加技术参数
```

### 多轮推理

```bash
# 第一轮：分析
# 第二轮：优先级排序
# 第三轮：行动计划
```

## 模型特定技巧

### Claude

- 擅长细微指令
- 对角色扮演响应良好
- 善于遵循复杂约束
- 偏好明确的输出格式

### GPT-4

- 代码生成能力强
- 示例效果良好
- 结构化输出好
- 响应 "let's think step by step"

## 常见错误

| 错误 | 问题 | 修复 |
|------|------|------|
| 太模糊 | 不可预测的输出 | 添加具体细节 |
| 太长 | 模型失去焦点 | 优先处理关键信息 |
| 矛盾 | 模型困惑 | 移除矛盾 |
| 无格式 | 输出不一致 | 指定格式 |
| 无示例 | 期望不明确 | 添加少样本 |

## 提示模板

### 代码审查

```
Review this [language] code for:
1. Bugs and logic errors
2. Security vulnerabilities
3. Performance issues
4. Code style/best practices

Code:
[code]

For each issue found, provide:
- Line number
- Issue description
- Severity (high/medium/low)
- Suggested fix
```

### 内容写作

```
Write a [content type] about [topic].

Audience: [target audience]
Tone: [formal/casual/professional]
Length: [word count]
Key points to cover:
1. [point 1]
2. [point 2]
3. [point 3]

Include: [specific elements]
Avoid: [things to exclude]
```
