# Install Skill — Claude Code Skill

教会 Claude Code 如何给自己安装新的 Skill。当你有一个 skill 文件夹想装进 Claude Code 时，这个 skill 会帮你完成所有步骤。

## 安装方法

### macOS / Linux

```bash
cp -r install-skill ~/.claude/skills/
```

### Windows (WSL)

```bash
cp -r install-skill ~/.claude/skills/
```

### Windows (PowerShell)

```powershell
Copy-Item -Recurse "install-skill" "$env:USERPROFILE\.claude\skills\install-skill"
```

## 使用方式

在 Claude Code 中输入：

```
/install-skill
```

Claude 会引导你完成以下步骤：

1. **选择来源** — 本地文件夹路径、git 仓库地址、或从零创建
2. **读取 skill** — 分析 SKILL.md 和依赖文件
3. **检查依赖** — 环境变量、CLI 工具、npm/pip 包
4. **安装** — 复制到 `~/.claude/skills/`
5. **配置** — 设置所需的环境变量
6. **验证** — 确认文件到位，脚本可执行

## 适用场景

- 从本地开发好的 skill 安装到 Claude Code
- 从 GitHub 克隆并安装社区 skill
- 让 Claude 帮你从零创建一个新 skill

## 依赖

无。纯指令型 skill，不依赖任何外部脚本或 API。

## 文件结构

```
install-skill/
├── SKILL.md           # Claude Code 指令文件（必需）
└── README-HUMAN.md    # 本文件（给人类看的）
```

## License

MIT
