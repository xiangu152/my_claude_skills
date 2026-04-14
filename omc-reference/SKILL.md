---
name: omc-reference
description: OMC agent 目录、可用工具、团队管道路由、提交协议和 skills 注册表。当委托 agent、使用 OMC 工具、协调团队、提交代码或调用 skills 时自动加载。
---

# OMC Reference

内置参考，需要详细的 OMC 目录信息时使用。

## Agent 目录

前缀：`oh-my-claudecode:`。完整的 prompts 参见 `agents/*.md`。

| Agent | 模型 | 用途 |
|-------|------|------|
| `explore` | haiku | 快速代码库搜索和映射 |
| `analyst` | opus | 需求清晰度和隐藏约束 |
| `planner` | opus | 排序和执行计划 |
| `architect` | opus | 系统设计、边界和长期权衡 |
| `debugger` | sonnet | 根因分析和故障诊断 |
| `executor` | sonnet | 实现和重构 |
| `verifier` | sonnet | 完成证据和验证 |
| `tracer` | sonnet | 追踪收集和证据捕获 |
| `security-reviewer` | sonnet | 信任边界和漏洞 |
| `code-reviewer` | opus | 全面的代码审查 |
| `test-engineer` | sonnet | 测试策略和回归覆盖 |
| `designer` | sonnet | UX 和交互设计 |
| `writer` | haiku | 文档和简洁内容 |
| `qa-tester` | sonnet | 运行时/手动验证 |
| `scientist` | sonnet | 数据分析和统计推理 |
| `document-specialist` | sonnet | SDK/API/框架文档查找 |
| `git-master` | sonnet | 提交策略和历史卫生 |
| `code-simplifier` | opus | 行为保留的简化 |
| `critic` | opus | 计划/设计挑战和审查 |

## 模型路由

- `haiku` — 快速查找、轻量检查、窄文档工作
- `sonnet` — 标准实现、调试和审查
- `opus` — 架构、深度分析、共识规划和高风险审查

## 工具参考

### 外部 AI / 编排
- `/team N:executor "task"`
- `/oh-my-claudecode:ask <claude|codex|gemini>`
- `/ccg`

### OMC 状态
- `state_read`, `state_write`, `state_clear`, `state_list_active`, `state_get_status`

### 团队运行时
- `TeamCreate`, `TeamDelete`, `SendMessage`, `TaskCreate`, `TaskList`, `TaskGet`, `TaskUpdate`

### 记事本
- `notepad_read`, `notepad_write_priority`, `notepad_write_working`, `notepad_write_manual`

### 项目内存
- `project_memory_read`, `project_memory_write`, `project_memory_add_note`, `project_memory_add_directive`

### 代码智能
- LSP: `lsp_hover`, `lsp_goto_definition`, `lsp_find_references`, `lsp_diagnostics`
- AST: `ast_grep_search`, `ast_grep_replace`
- 工具: `python_repl`

## Skills 注册表

通过 `/oh-my-claudecode:<name>` 调用内置工作流。

### 工作流 skills
- `autopilot` — 从想法到工作代码的完全自主执行
- `ralph` — 持续循环直到完成验证
- `ultrawork` — 高吞吐量并行执行
- `team` — 协调团队编排
- `ccg` — Codex + Gemini + Claude 综合
- `ultraqa` — QA 循环：测试、验证、修复、重复
- `omc-plan` — 规划工作流

### 实用 skills
- `ask`, `cancel`, `note`, `learner`, `omc-setup`, `mcp-setup`, `hud`, `trace`

## 团队管道

阶段：`team-plan` → `team-prd` → `team-exec` → `team-verify` → `team-fix`（循环）

## 提交协议

使用 git trailers 保留决策上下文。

### 格式
- Intent 行优先：为什么做这个更改
- 可选正文包含上下文和理由
- 适用时使用结构化 trailers

### 常用 trailers
- `Constraint:` 活跃约束
- `Rejected:` 被拒绝的替代方案及原因
- `Directive:` 前瞻性警告或指示
- `Confidence:` `high` | `medium` | `low`
- `Scope-risk:` `narrow` | `moderate` | `broad`

### 示例
```text
feat(docs): reduce instruction footprint

移动仅参考的编排内容到原生 skill

Constraint: 保留 CLAUDE.md 标记安装流程
Rejected: 同步所有内置 skills | 行为变化大于需求
Confidence: high
Scope-risk: narrow
```
