# Context Guardian — Claude Code Skill

防止 Claude Code 在上下文压缩（compact）后产生幻觉。通过 checkpoint 机制和用户确认协议，确保压缩后工作状态正确。

## 解决的问题

Claude Code 的 compact 功能会压缩对话历史以节省上下文窗口。压缩后：
- 最近的详细工作可能被摘要或丢失
- 模型可能"记住"没发生过的事
- 模型可能从错误假设继续
- 模型可能硬编码它认为有效但实际没验证过的方案

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 无其他依赖

## 安装到 Claude Code

```bash
cp -r context-guardian ~/.claude/skills/
```

## 工作原理

```
任务开始 → 创建 checkpoint
  ↓
工作 → 每个里程碑更新 checkpoint
  ↓
上下文压缩（检测到或怀疑）
  ↓
停止 → 读 checkpoint → 向用户展示状态 → 等待确认
  ↓
用户确认 → 从验证过的状态继续
```

## 核心机制

### Checkpoint 文件

多步骤任务开始时，在项目目录创建 `.checkpoints/current-task.md`，记录：
- 任务描述和原始请求
- 分步计划（含完成状态）
- 每步的具体结果
- 修改的文件清单
- 关键决策

每次完成有意义的步骤后更新。

### 压缩检测

无法直接检测 compact，通过以下信号判断：

**强信号（立即停止）：**
- 用户说 "compact"、"上下文压缩了"、"你忘了"
- 用户说 "确认进度"

**弱信号（检查 checkpoint）：**
- 不确定当前在哪一步
- 不记得为什么修改了某个文件
- 有"直接继续"的冲动而不验证

### 验证模板

检测到压缩后，向用户展示：
- 当前任务
- 已完成/进行中/待做的步骤
- 关键决策
- 修改的文件

**必须用户明确确认才能继续。**

## 任务模板

内置三种模板，按需选用：
- **Prompt Tuning** — prompt 调优专用（含逻辑摘要、case 表、变更日志）
- **Code Development** — 代码开发通用
- **Data Processing** — 数据处理专用

## 触发方式

自动：多步骤任务（>10 turn）时主动创建 checkpoint
手动：
- "确认一下进度"
- "你之前在做什么"
- "checkpoint"

## 文件结构

```
context-guardian/
├── SKILL.md                    # 指令文件
├── README-HUMAN.md             # 本文件
└── assets/
    └── checkpoint-template.md  # checkpoint 模板
```

## License

MIT
