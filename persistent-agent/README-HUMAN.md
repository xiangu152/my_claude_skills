# Persistent Agent — Claude Code Skill

让 Claude Code 具备跨会话持久化能力：记忆、身份、自学习。每次打开终端自动恢复上下文。

## 核心理念

Claude Code 会话是临时的——关闭终端 = 进程 kill。此 skill 通过文件系统实现持久化：

- **身份**：SOUL.md 定义我是谁
- **用户**：USER.md 记录我在帮谁
- **记忆**：MEMORY.md + memory/ 每日日志
- **学习**：.learnings/ 记录错误、纠正、洞察

没有心跳、没有网关、没有后台进程。打开终端 → 读文件恢复 → 工作 → 关闭 → 文件保存。下次再来。

## 安装

### 1. 安装 skill

```bash
cp -r persistent-agent ~/.claude/skills/
```

### 2. 初始化工作空间

```bash
mkdir -p ~/.claude/workspace/memory ~/.claude/workspace/.learnings
cp ~/.claude/skills/persistent-agent/assets/*.md ~/.claude/workspace/
cp -r ~/.claude/skills/persistent-agent/assets/.learnings/* ~/.claude/workspace/.learnings/
```

### 3. 在项目目录创建 CLAUDE.md 入口

在你的项目根目录创建 `CLAUDE.md`：

```markdown
# Persistent Agent

Read and follow: ~/.claude/skills/persistent-agent/SKILL.md

Every session start:
1. Read ~/.claude/workspace/SOUL.md
2. Read ~/.claude/workspace/USER.md
3. Read ~/.claude/workspace/MEMORY.md
4. Read ~/.claude/workspace/memory/$(date +%Y-%m-%d).md
```

或在 `~/.claude/CLAUDE.md` 创建全局入口（所有项目生效）。

### 4. 重启 Claude Code

退出并重新运行 `claude`，启动序列自动生效。

## 会话生命周期

```
打开终端 → 读文件恢复上下文 → 工作（读写文件）→ 关闭终端 → 文件保存
                                                                    ↓
                              下次打开终端 ← ← ← ← ← ← ← ← ← ← ←
```

## 文件结构

### 工作空间 `~/.claude/workspace/`

| 文件 | 用途 |
|---|---|
| SOUL.md | 人格、语气、原则 |
| USER.md | 用户信息、偏好 |
| AGENTS.md | 工作规则、启动序列 |
| TOOLS.md | 环境特定配置 |
| MEMORY.md | 长期记忆（curated） |
| memory/YYYY-MM-DD.md | 每日记忆（raw log） |
| .learnings/LEARNINGS.md | 纠正、洞察 |
| .learnings/ERRORS.md | 命令失败 |
| .learnings/FEATURE_REQUESTS.md | 功能需求 |

### Skill 文件

```
persistent-agent/
├── SKILL.md           # 指令文件
├── README-HUMAN.md    # 本文件
└── assets/            # 模板文件
    ├── SOUL.md
    ├── USER.md
    ├── AGENTS.md
    ├── TOOLS.md
    ├── MEMORY.md
    └── .learnings/
        ├── LEARNINGS.md
        ├── ERRORS.md
        └── FEATURE_REQUESTS.md
```

## License

MIT
