# Self-Improvement — Claude Code Skill

让 Claude Code 具备持续学习能力，自动记录错误、纠正和经验，促进到项目记忆中。

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 无其他依赖

## 安装到 Claude Code

```bash
cp -r self-improvement ~/.claude/skills/
```

## 使用方式

此 skill 为被动型，Claude Code 在以下场景自动触发：

| 场景 | 记录位置 |
|------|----------|
| 命令执行失败 | `.learnings/ERRORS.md` |
| 用户纠正 Claude | `.learnings/LEARNINGS.md` |
| 用户提出缺失功能 | `.learnings/FEATURE_REQUESTS.md` |
| 发现更好的方法 | `.learnings/LEARNINGS.md` |
| 知识过时/错误 | `.learnings/LEARNINGS.md` |

## 首次初始化

Claude 会在首次使用时自动创建 `.learnings/` 目录和三个日志文件：

```
.learnings/
├── LEARNINGS.md          # 纠正、洞察、知识缺口、最佳实践
├── ERRORS.md             # 命令失败和集成错误
└── FEATURE_REQUESTS.md   # 用户提出的功能需求
```

## 学习促进

当某个 learning 被验证广泛适用时，Claude 会将其促进到：

| 类型 | 促进目标 |
|------|----------|
| 行为模式 | `CLAUDE.md` |
| 工作流改进 | `AGENTS.md` |
| 工具注意事项 | `TOOLS.md` |

## 可选：Hook 集成

在 `.claude/settings.json` 中添加 hook 配置，实现自动提醒：

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "./skills/self-improvement/scripts/activator.sh"
      }]
    }]
  }
}
```

## 文件结构

```
self-improvement/
├── SKILL.md              # Claude Code 指令文件
├── README-HUMAN.md       # 本文件
├── assets/               # 模板文件
│   ├── ERRORS.md
│   ├── FEATURE_REQUESTS.md
│   ├── LEARNINGS.md
│   └── SKILL-TEMPLATE.md
└── scripts/              # Hook 脚本
    ├── activator.sh
    ├── error-detector.sh
    └── extract-skill.sh
```

## License

原仓库：https://github.com/pskoett/pskoett-ai-skills
