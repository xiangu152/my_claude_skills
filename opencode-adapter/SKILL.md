---
name: opencode-adapter
description: 验证和适配 Claude Code skills 使其兼容 OpenCode。用于：（1）检查 skill 是否在 Claude Code 和 OpenCode 中都能工作；（2）在 OpenCode 中测试 skill；（3）检测平台特定问题。触发词：'opencode'、'opencode 兼容'、'skill 兼容'、'跨平台 skill'。NOT for：创建新 skill（用 skill-creator）、安装 skill（用 install-skill）。
---

# OpenCode Adapter

验证 Claude Code skills 是否在 Claude Code 和 OpenCode 中都兼容。

## 好消息

OpenCode 从 `~/.claude/skills/` 读取 skills，使用与 Claude Code 完全相同的格式：
- 相同的 YAML frontmatter（`name`、`description`）
- 相同的目录结构（`SKILL.md`、`scripts/`、`references/`、`assets/`）
- 相同的安装位置（`~/.claude/skills/`）

**Skills 默认跨平台兼容。** 此 skill 帮助检测边缘情况。

## 兼容性检查

### Step 1: 列出两边的 Skills

```bash
# Claude Code / OpenCode skills
ls ~/.claude/skills/
```

对比两个列表，有缺失吗？

### Step 2: 检查 Frontmatter

OpenCode 要求与 Claude Code 相同的字段：

```bash
for skill in ~/.claude/skills/*/SKILL.md; do
  name=$(basename $(dirname $skill))
  has_name=$(head -5 $skill | grep "^name:")
  has_desc=$(head -10 $skill | grep "^description:")

  if [ -z "$has_name" ]; then
    echo "❌ $name: missing 'name' in frontmatter"
  elif [ -z "$has_desc" ]; then
    echo "❌ $name: missing 'description' in frontmatter"
  else
    echo "✅ $name"
  fi
done
```

### Step 3: 在 OpenCode 中测试

对每个 skill，运行快速测试：

```bash
opencode run "使用 [skill-name] skill 做 [简单测试]" --model xiaomi/mimo-v2-flash
```

### Step 4: 检测差异

| 检查项 | Claude Code | OpenCode |
|-------|-------------|----------|
| Skill 位置 | `~/.claude/skills/` | `~/.claude/skills/` ✅ 相同 |
| Frontmatter 格式 | YAML `name` + `description` | YAML `name` + `description` ✅ 相同 |
| 目录结构 | SKILL.md + scripts/ 等 | SKILL.md + scripts/ 等 ✅ 相同 |
| 触发方式 | Description 匹配 | Description 匹配 ✅ 相同 |
| 脚本执行 | Bash/Node/Python | Bash/Node/Python ✅ 相同 |
| 环境变量 | `~/.zshrc` / `~/.bashrc` | `~/.zshrc` / `~/.bashrc` ✅ 相同 |

### Step 5: 报告

```markdown
## 兼容性报告

| Skill | Claude Code | OpenCode | 问题 |
|-------|-------------|----------|------|
| agent-browser | ✅ | ✅ | 无 |
| excel-xlsx | ✅ | ✅ | 无 |
| ... | ... | ... | ... |
```

## 已知差异

| 方面 | Claude Code | OpenCode |
|------|------------|----------|
| 默认模型 | Sonnet/Opus | 可配置 |
| API provider | Anthropic | 多 provider |
| 上下文压缩 | auto-compact | 可能不同 |
| Hook 系统 | `.claude/settings.json` | 可能不同 |
| MCP 支持 | 有 | 有（`opencode mcp`） |

## 适配指南

大多数 skills 无需任何适配。如果出现问题：

### 1. 模型特定指令

如果 skill 引用 Claude 特定模型，添加 OpenCode 替代方案：

```markdown
## 前置条件
- Claude Code: 使用默认模型
- OpenCode: `opencode run "..." --model xiaomi/mimo-v2-flash`
```

### 2. 平台特定路径

如果 skill 使用平台特定路径，确保两者都有文档：

```bash
# 两者都使用 ~/.claude/skills/ — 无需更改
```

### 3. 环境变量

两者都从 `~/.zshrc` 读取 — 无需更改。

## 批量验证

一次性检查所有 skills：

```bash
echo "=== Skills 兼容性检查 ==="
ls ~/.claude/skills/*/SKILL.md | while read f; do
  name=$(basename $(dirname $f))
  echo -n "$name: "
  head -3 "$f" | grep -q "^name:" && echo "✅" || echo "❌"
done
```
