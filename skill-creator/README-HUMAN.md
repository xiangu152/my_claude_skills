# Skill Creator — Claude Code Skill

让 Claude Code 具备创建、编辑、审查 skill 的能力。包含 skill 设计规范、最佳实践和创建流程。

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 无其他依赖

## 安装到 Claude Code

```bash
cp -r skill-creator ~/.claude/skills/
```

## 使用方式

在 Claude Code 中直接说需要创建或修改 skill，Claude 会自动调用此 skill。

### 适用场景

- 从零创建新 skill
- 改进现有 skill 的 SKILL.md
- 审查 skill 质量
- 重组 skill 目录结构
- 优化 description 以改善触发效果

### 触发方式

自然语言触发：
- "帮我创建一个 skill 来做 XXX"
- "审查一下这个 skill"
- "改进这个 skill 的 description"
- "把这段知识提取成 skill"

## 核心知识

此 skill 教 Claude Code 掌握：

1. **Skill 结构规范** — SKILL.md frontmatter、body、scripts/references/assets 目录
2. **设计原则** — 简洁优先、渐进式披露、适当的自由度
3. **创建流程** — 理解需求 → 规划资源 → 初始化 → 编写 → 测试 → 迭代
4. **命名规范** — 小写+连字符，动词优先

## 文件结构

```
skill-creator/
├── SKILL.md           # Claude Code 指令文件
└── README-HUMAN.md    # 本文件
```

## License

MIT
