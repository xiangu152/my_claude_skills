# Tavily Search — Claude Code Skill

让 Claude Code 具备联网搜索能力，基于 [Tavily](https://tavily.com) 的 LLM 优化搜索 API。

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 已注册 Tavily 并获取 API Key（免费额度足够个人使用）
- 已设置环境变量 `TAVILY_API_KEY`（见下方说明）

## 安装方法

### macOS / Linux

1. 打开终端，将整个 `tavily-search` 文件夹复制到 Claude Code 个人技能目录：

```bash
cp -r tavily-search ~/.claude/skills/
```

2. 确认文件结构正确：

```
~/.claude/skills/tavily-search/
├── SKILL.md
└── scripts/
    └── search.mjs
```

3. 设置环境变量（如果还没设置过）：

```bash
echo 'export TAVILY_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

如果你用的是 bash，把 `~/.zshrc` 换成 `~/.bashrc`。

### Windows

Claude Code 在 Windows 上通常通过 WSL (Windows Subsystem for Linux) 运行，安装方式与 Linux 相同：

```bash
cp -r tavily-search ~/.claude/skills/
echo 'export TAVILY_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

如果直接在 PowerShell 中使用 Claude Code，则手动复制文件夹到：

```
C:\Users\你的用户名\.claude\skills\tavily-search\
```

并设置环境变量：

```powershell
# 永久设置（当前用户）
[Environment]::SetEnvironmentVariable("TAVILY_API_KEY", "your-api-key-here", "User")
```

## 验证安装

重启 Claude Code 后，输入：

```
/tavily-search
```

如果 Claude 能列出搜索选项，说明安装成功。你也可以直接提问让它搜索，它会自动调用这个 skill。

## 使用方式

两种方式触发搜索：

1. **自动触发** — 直接问 Claude 需要联网搜索的问题，比如「搜索最新的 React 19 特性」
2. **手动触发** — 输入 `/tavily-search` 后跟搜索内容

### 搜索选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-n <数量>` | 结果数量 (1-20) | 10 |
| `--depth <模式>` | 搜索深度：`ultra-fast` / `fast` / `basic` / `advanced` | `basic` |
| `--topic <类型>` | `general`（通用）或 `news`（新闻） | `general` |
| `--time-range <范围>` | 时间范围：`day` / `week` / `month` / `year` | 不限 |
| `--include-domains <域名>` | 限定搜索域名（逗号分隔） | 不限 |
| `--exclude-domains <域名>` | 排除域名（逗号分隔） | 不限 |

## 文件结构

```
tavily-search/
├── SKILL.md           # Claude Code 指令文件（必需）
├── README-HUMAN.md    # 本文件（给人类看的）
└── scripts/
    └── search.mjs     # Tavily API 搜索脚本
```

## License

MIT
