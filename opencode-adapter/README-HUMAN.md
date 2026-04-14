# OpenCode Adapter — Claude Code Skill

验证 Claude Code skill 在 OpenCode 中的兼容性，检测平台差异。

## 发现

OpenCode 和 Claude Code **共享完全相同的 skill 格式**：
- 同样的 YAML frontmatter（`name` + `description`）
- 同样的目录结构（`SKILL.md` + `scripts/` + `references/` + `assets/`）
- 同样的安装位置（`~/.claude/skills/`）

**skill 不需要翻译，直接兼容。**

## 前置条件

- 已安装 Claude Code
- 已安装 OpenCode
- 无其他依赖

## 安装到 Claude Code

```bash
cp -r opencode-adapter ~/.claude/skills/
```

## 使用方式

### 兼容性检查

对 Claude Code 或 OpenCode 说：
- "检查所有 skill 在 OpenCode 中的兼容性"
- "opencode 兼容"

### 验证流程

1. 列出两个平台的 skill，对比
2. 检查每个 SKILL.md 的 frontmatter 格式
3. 在 OpenCode 中测试执行
4. 生成兼容性报告

### 已知差异

| 方面 | Claude Code | OpenCode |
|------|------------|----------|
| 默认模型 | Anthropic Sonnet/Opus | 可配置（Xiaomi/等） |
| 上下文压缩 | auto-compact | 行为可能不同 |
| Hook 系统 | `.claude/settings.json` | 可能不同 |

## 文件结构

```
opencode-adapter/
├── SKILL.md           # Claude Code 指令文件
└── README-HUMAN.md    # 本文件
```

## License

MIT
