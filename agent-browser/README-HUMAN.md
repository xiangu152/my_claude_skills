# Agent Browser — Claude Code Skill

基于 accessibility tree 的无头浏览器自动化工具，通过 ref 精确定位元素，适合 AI agent 驱动的网页操作。

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 已安装 Node.js
- 已安装 agent-browser CLI

## 安装

```bash
npm install -g agent-browser
agent-browser install --with-deps
```

## 安装到 Claude Code

```bash
cp -r agent-browser ~/.claude/skills/
```

## 验证

```bash
agent-browser --version
```

## 使用方式

在 Claude Code 中直接提问涉及网页自动化的任务，Claude 会自动调用此 skill。

## 核心工作流

1. `agent-browser open <url>` — 打开页面
2. `agent-browser snapshot -i --json` — 获取可交互元素快照
3. 通过 `@eN` 引用操作元素（click、fill、type 等）
4. 重新 snapshot 验证页面变化

## 文件结构

```
agent-browser/
├── SKILL.md           # Claude Code 指令文件
└── README-HUMAN.md    # 本文件
```

## License

原作者：Yossi Elkrief ([@MaTriXy](https://github.com/MaTriXy))
CLI 来源：[Vercel Labs](https://github.com/vercel-labs/agent-browser)
