# Claude Code Skills

一组为 Claude Code 设计的可复用技能（Skills），覆盖浏览器自动化、文档处理、搜索、专利撰写、持续记忆、代码优化等场景。

## 安装

每个 skill 都是独立目录，包含一个 `SKILL.md` 入口文件。将整个目录复制到 `$HOME/.claude/skills/` 即可：

```bash
cp -r <skill-name> ~/.claude/skills/
```

也可使用仓库自带的 `install-skill` 技能辅助安装。

## Skills 列表

### 核心工具

| Skill | 说明 | 依赖 |
|-------|------|------|
| [agent-browser](agent-browser/) | 无头浏览器自动化，支持无障碍树快照、元素交互、截图/PDF | `npm install -g agent-browser` |
| [tavily-search](tavily-search/) | 使用 Tavily API 进行 LLM 优化的网络搜索 | `TAVILY_API_KEY` |
| [web-search](web-search/) | 通过 inference.sh CLI 进行 Web 搜索和内容提取（Tavily/Exa）| `infsh` CLI |
| [web-research](web-research/) | 通过子代理进行系统化 Web 研究，生成带引用的报告 | — |

### 文档处理

| Skill | 说明 | 依赖 |
|-------|------|------|
| [excel-xlsx](excel-xlsx/) | 创建、查看、编辑 Excel 工作簿（XLSX/XLSM）| `pip install openpyxl pandas` |
| [word-docx](word-docx/) | 创建、查看、编辑 Word 文档（DOCX）| `pip install python-docx lxml` |
| [nano-pdf](nano-pdf/) | 用自然语言编辑 PDF 指定页面 | `pip install nano-pdf` |
| [feishu](feishu/) | 飞书开放 API 集成：文档、云盘、权限、知识库、多维表格 | 飞书应用凭证 |

### AI 与 ML

| Skill | 说明 | 依赖 |
|-------|------|------|
| [fine-tuning-expert](fine-tuning-expert/) | LLM 微调专家：LoRA/QLoRA、PEFT、数据集准备、超参数调优 | transformers, peft, trl |
| [prompt-engineering](prompt-engineering/) | AI 模型提示工程指南：LLM、图像生成、视频模型提示技巧 | `infsh` CLI |
| [prompt-tuner](prompt-tuner/) | 结构化 prompt 调优流程，逻辑优先 | — |
| [rag-retrieval](rag-retrieval/) | RAG 模式：混合搜索、上下文检索、HyDE、Agentic RAG、重排、PGVector | — |

### 代码优化

| Skill | 说明 | 依赖 |
|-------|------|------|
| [spark-optimization](spark-optimization/) | Apache Spark 作业优化：分区策略、缓存、shuffle、内存调优 | pyspark |

### 搜索与研究

| Skill | 说明 | 依赖 |
|-------|------|------|
| [find-skills](find-skills/) | 发现和安装 agent skills，搜索 skills 生态 | — |
| [parallel-deep-research](parallel-deep-research/) | 深度研究工具：通过 parallel-cli 进行深入调查 | `parallel-cli` |

### 记忆与持久化

| Skill | 说明 | 依赖 |
|-------|------|------|
| [persistent-agent](persistent-agent/) | 持久化 Agent：跨会话记忆、身份、自我学习 | — |
| [context-guardian](context-guardian/) | 防止上下文压缩导致的幻觉，通过 checkpoint 追踪任务进度 | — |
| [self-improvement](self-improvement/) | 记录错误、纠正与学习，持续改进 | — |
| [self-improving-agent](self-improving-agent/) | 通用自我改进 agent，多内存架构自动从经验学习 | — |

### Skill 开发

| Skill | 说明 | 依赖 |
|-------|------|------|
| [skill-creator](skill-creator/) | 创建、编辑、审核 Claude Code skill 的指南 | — |
| [skill-translator](skill-translator/) | 将 OpenClaw skill 翻译为 Claude Code 格式 | — |
| [skillquality-analyzer](skillquality-analyzer/) | Claude Skills 综合质量分析，五个维度评估 | skill-security-analyzer |
| [skill-security-analyzer](skill-security-analyzer/) | Claude Skills 安全分析，检测 40+ 恶意模式 | — |

### 平台集成

| Skill | 说明 | 依赖 |
|-------|------|------|
| [opencode-adapter](opencode-adapter/) | 验证和适配 Claude Code skills 使其兼容 OpenCode | — |
| [omc-reference](omc-reference/) | OMC agent 目录、工具、团队管道路由、skills 注册表 | — |

### 其他

| Skill | 说明 | 依赖 |
|-------|------|------|
| [install-skill](install-skill/) | 辅助将 skill 安装到 Claude Code | — |
| [patent-writer](patent-writer/) | 基于代码库撰写中国专利申请书（DOCX 输出）| tavily-search, word-docx |
| [ssh-essentials](ssh-essentials/) | SSH 全面参考：连接、密钥、端口转发、文件传输 | — |
| [startup-compiler](startup-compiler/) | 将任务编译为可执行单元，支持定时和文件监控触发 | — |

## 目录结构

```
my_claude_skills/
├── agent-browser/
│   └── SKILL.md              # 入口：触发条件、指令
├── context-guardian/
├── excel-xlsx/
├── feishu/
│   └── scripts/              # 飞书 API 脚本
├── find-skills/
├── fine-tuning-expert/
│   └── references/          # 微调参考文档
├── install-skill/
├── nano-pdf/
├── omc-reference/
├── opencode-adapter/
├── parallel-deep-research/
├── patent-writer/
├── persistent-agent/
├── prompt-engineering/
├── prompt-tuner/
├── rag-retrieval/
│   └── rules/               # RAG 模式规则
├── self-improvement/
├── self-improving-agent/
│   ├── hooks/               # 钩子脚本
│   ├── memory/              # 内存结构
│   └── references/
├── skill-creator/
├── skillquality-analyzer/
│   └── references/
├── skill-security-analyzer/
│   ├── scripts/             # 扫描器脚本
│   └── tests/
├── skill-translator/
├── spark-optimization/
├── ssh-essentials/
├── startup-compiler/
│   ├── DESIGN.md
│   ├── assets/
│   └── dispatcher/
├── tavily-search/
├── web-research/
├── web-search/
├── word-docx/
└── README.md
```

## Skill 结构约定

每个 skill 目录包含：

- **SKILL.md** — 核心入口，定义触发条件、指令和资源引用。Claude Code 根据 description 自动匹配触发。
- **scripts/** — 运行时脚本（Node.js / Python / Bash），通过 `$SCRIPT_DIR` 引用。
- **references/** — 详细参考文档。
- **assets/** — 模板、静态资源等辅助文件。

## 使用方式

Skills 安装后，Claude Code 会根据 frontmatter 中的 `description` 自动匹配。你也可以在对话中直接说明要使用的 skill：

```
帮我用 patent-writer 撰写一个关于 XXX 的专利
用 fine-tuning-expert 帮我配置一个 LoRA 微调
用 parallel-deep-research 研究一下最新的 AI Agent 进展
```

## 适用环境

- Claude Code CLI / VS Code 扩展
- macOS / Windows / Linux
