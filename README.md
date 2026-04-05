# Claude Code Skills

一组为 Claude Code 设计的可复用技能（Skills），覆盖浏览器自动化、文档处理、搜索、专利撰写、持续记忆等场景。

## 安装

每个 skill 都是独立目录，包含一个 `SKILL.md` 入口文件。将整个目录复制到 `$HOME/.claude/skills/` 即可：

```bash
cp -r <skill-name> ~/.claude/skills/
```

也可使用仓库自带的 `install-skill` 技能辅助安装。

## Skills 列表

| Skill | 说明 | 依赖 |
|-------|------|------|
| [agent-browser](agent-browser/) | 无头浏览器自动化，支持无障碍树快照、元素交互、截图/PDF | `npm install -g agent-browser` |
| [context-guardian](context-guardian/) | 防止上下文压缩导致的幻觉，通过 checkpoint 文件追踪任务进度 | — |
| [excel-xlsx](excel-xlsx/) | 创建、查看、编辑 Excel 工作簿（XLSX/XLSM） | `pip install openpyxl pandas` |
| [feishu](feishu/) | 飞书开放 API 集成：文档、云盘、权限、知识库、多维表格 | 飞书应用凭证 |
| [install-skill](install-skill/) | 辅助将 skill 安装到 Claude Code | — |
| [nano-pdf](nano-pdf/) | 用自然语言编辑 PDF 指定页面 | `pip install nano-pdf` |
| [patent-writer](patent-writer/) | 基于代码库撰写中国专利申请书（DOCX 输出） | tavily-search, word-docx |
| [persistent-agent](persistent-agent/) | 持久化 Agent：跨会话记忆、身份、自我学习 | — |
| [prompt-tuner](prompt-tuner/) | 结构化 prompt 调优流程，逻辑优先 | — |
| [self-improvement](self-improvement/) | 记录错误、纠正与学习，持续改进 | — |
| [skill-creator](skill-creator/) | 创建、编辑、审核 Claude Code skill 的指南 | — |
| [skill-translator](skill-translator/) | 将 OpenClaw skill 翻译为 Claude Code 格式 | — |
| [ssh-essentials](ssh-essentials/) | SSH 全面参考：连接、密钥、端口转发、文件传输 | — |
| [startup-compiler](startup-compiler/) | 将任务编译为可执行单元，支持定时和文件监控触发 | — |
| [tavily-search](tavily-search/) | 使用 Tavily API 进行 LLM 优化的网络搜索 | `TAVILY_API_KEY` |
| [word-docx](word-docx/) | 创建、查看、编辑 Word 文档（DOCX） | `pip install python-docx lxml` |

## 目录结构

```
my_claude_skills/
├── agent-browser/
│   ├── SKILL.md            # 入口：触发条件、指令、脚本引用
│   └── README-HUMAN.md     # 人类可读文档
├── context-guardian/
├── excel-xlsx/
├── feishu/
│   └── scripts/            # 运行时脚本
├── install-skill/
├── nano-pdf/
├── patent-writer/
├── persistent-agent/
├── prompt-tuner/
├── self-improvement/
├── skill-creator/
├── skill-translator/
├── ssh-essentials/
├── startup-compiler/
│   ├── DESIGN.md           # 设计文档
│   ├── assets/             # 模板
│   └── dispatcher/         # 调度器
├── tavily-search/
│   └── scripts/
├── word-docx/
├── dispatcher/             # 全局调度基础设施
└── README.md
```

## Skill 结构约定

每个 skill 目录包含：

- **SKILL.md** — 核心入口，定义触发条件、指令和资源引用。Claude Code 启动时加载 frontmatter 元数据，触发时加载完整内容。
- **README-HUMAN.md** — 面向人类的使用说明（中文）。
- **scripts/** — 运行时脚本（Node.js / Python），通过 `$SCRIPT_DIR` 引用。
- **assets/** — 模板、静态资源等辅助文件。

## 使用方式

Skills 安装后，Claude Code 会根据 frontmatter 中的 `trigger` 字段自动匹配。你也可以在对话中通过 `/skill-name` 手动触发，例如：

```
/agent-browser
/tavily-search "deepseek latest news"
/word-docx
```

## 适用环境

- Claude Code CLI / VS Code 扩展
- macOS / Windows / Linux
