# Skill Translator — Claude Code Skill

让 Claude Code 学会将 OpenClaw skill 翻译/转换为 Claude Code 兼容的 skill 格式。

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 无其他依赖

## 安装到 Claude Code

```bash
cp -r skill-translator ~/.claude/skills/
```

## 使用方式

在 Claude Code 中直接说需要翻译/转换 skill，Claude 会自动调用此 skill。

### 触发方式

- "把 OpenClaw 的 xxx skill 转成 Claude Code 版本"
- "翻译这个 skill"
- "适配这个 skill 到 Claude Code"

### 翻译流程

此 skill 教 Claude Code 执行 6 步翻译：

1. **读取源 skill** — 读 OpenClaw SKILL.md + 列出所有文件
2. **创建目标目录** — 按需创建 scripts/references/assets
3. **翻译 SKILL.md** — 清理 frontmatter、移除 OpenClaw 特有语法、替换路径变量
4. **复制资源文件** — scripts/、references/、assets/ 原样复制
5. **创建 README-HUMAN.md** — 中文说明文档
6. **验证** — 检查文件结构、frontmatter 格式、无残留 OpenClaw 语法

### 核心转换规则

| OpenClaw | Claude Code |
|---|---|
| frontmatter 含 slug/version/homepage/changelog/metadata | 只保留 name + description |
| `{baseDir}` | `$SCRIPT_DIR` 或相对路径 |
| `clawhub install xxx` | `cp -r xxx ~/.claude/skills/` |
| `skills.entries` JSON 配置 | 环境变量 export |
| 可选的用户文档 | 必须有 README-HUMAN.md（中文） |

## 文件结构

```
skill-translator/
├── SKILL.md           # Claude Code 指令文件
└── README-HUMAN.md    # 本文件
```

## License

MIT
