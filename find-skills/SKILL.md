---
name: find-skills
description: 帮助用户发现和安装 agent skills。当用户询问"如何做 X"、"找一个做 X 的 skill"、"有没有能...的 skill"，或表达想扩展能力时触发此 skill。
---

# Find Skills

此 skill 帮助你在 Claude Code skills 生态中发现和安装技能。

## 何时使用此 Skill

当用户：

- 询问"如何做 X"（X 可能有现成的 skill）
- 说"找一个做 X 的 skill"或"有没有做 X 的 skill"
- 询问"你能做 X 吗"（X 是专业能力）
- 表达想扩展 agent 能力
- 想搜索工具、模板或工作流
- 提到希望有特定领域的帮助（设计、测试、部署等）

## Skills 生态系统

Skills 是模块化包，通过专门的知识、工作流和工具扩展 agent 能力。

**浏览 skills：** https://skills.claude.com/

**安装方式：**
```bash
cp -r skill-name "$HOME/.claude/skills/"
```

## 如何帮助用户找到 Skills

### Step 1: 了解需求

识别：
1. 领域（如 React、测试、设计、部署）
2. 具体任务（如写测试、创建动画、审查 PR）
3. 是否是足够常见的任务（很可能已有 skill）

### Step 2: 先检查热门 Skills

在运行搜索前，查看 [Claude Code Skills 目录](https://skills.claude.com/) 是否有知名 skill。

例如，Web 开发的热门 skills：
- `vercel-labs/agent-skills` — React、Next.js、Web 设计
- `anthropics/skills` — 前端设计、文档处理

### Step 3: 搜索 Skills

使用关键词搜索：
```bash
# 在 skills.claude.com 搜索
```

或使用 `/oh-my-claudecode:ask` 询问可用 skills。

### Step 4: 验证质量后再推荐

**不要仅基于搜索结果推荐 skill。** 始终验证：

1. **安装量** — 优先选择 1K+ 安装的 skill
2. **来源可靠性** — 官方来源更可信
3. **GitHub stars** — 检查源仓库

### Step 5: 向用户展示选项

找到相关 skills 后，展示：
1. Skill 名称和功能
2. 安装量和来源
3. 安装命令
4. 相关链接

示例：

```
找到一个可能帮助的 skill！"react-best-practices" skill 提供来自
Vercel Engineering 的 React 和 Next.js 性能优化指南。

安装：
cp -r react-best-practices "$HOME/.claude/skills/"
```

### Step 6: 提供安装帮助

如果用户想继续，可以帮他们安装：

```bash
cp -r <owner/repo> "$HOME/.claude/skills/"
```

## 常见 Skill 类别

搜索时考虑这些常见类别：

| 类别 | 示例查询 |
|------|----------|
| Web 开发 | react, nextjs, typescript, css, tailwind |
| 测试 | testing, jest, playwright, e2e |
| DevOps | deploy, docker, kubernetes, ci-cd |
| 文档 | docs, readme, changelog, api-docs |
| 代码质量 | review, lint, refactor, best-practices |
| 设计 | ui, ux, design-system, accessibility |
| 效率 | workflow, automation, git |

## 有效搜索的技巧

1. **使用具体关键词**："react testing" 比单独 "testing" 更好
2. **尝试替代术语**："deploy" 不行试试 "deployment"
3. **检查热门来源**：很多 skills 来自 `vercel-labs/agent-skills`

## 未找到 Skills 时

如果没有相关 skills：

1. 承认未找到匹配
2. 提供直接用通用能力帮助用户
3. 建议用户可以自己创建 skill

示例：

```
我搜索了与"xyz"相关的 skills，但没有找到匹配。
我仍然可以直接帮助你完成这个任务！想让我继续吗？

如果这是你经常做的事情，可以用以下方式创建自己的 skill
```

## 相关资源

- [Claude Code Skills 目录](https://skills.claude.com/)
- [创建新 Skill](skill-creator)
