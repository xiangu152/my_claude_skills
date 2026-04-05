# Startup Compiler — Claude Code Skill

将任务编译为可执行单元，包含隔离的环境、打包的 skills、不可变的执行日志。

## 核心规则

| 规则 | 说明 |
|------|------|
| 任务隔离 | 每个任务只知道自己的配置 |
| 注册表不删 | `task-manifest.json` 只增改查，不删除 |
| 日志 append-only | 执行日志只增查，不删改 |
| 先试跑再注册 | 验证环境 → 测试执行 → 用户确认 → 注册 |
| 无网关 | 本地调度器，无端口、无 HTTP、无 webhook |

## 前置条件

- 已安装 [Claude Code](https://code.claude.com)
- 已安装 Node.js（文件监控调度器需要）
- Python 3（定时调度器需要）

## 安装到 Claude Code

```bash
cp -r startup-compiler ~/.claude/skills/
```

## 初始化项目

在项目目录执行：

```bash
mkdir -p dispatcher output logs .claude
echo '{"tasks": []}' > task-manifest.json
cp ~/.claude/skills/startup-compiler/dispatcher/* dispatcher/
chmod +x dispatcher/dispatch.py
```

## 使用方式

### 编译任务

对 Claude Code 说：

> "帮我编译一个任务，每天 9 点读取 logs 生成日报"

Claude 会：
1. 确认需求（任务、环境、交付、触发方式）
2. 验证依赖（env vars、tools、files、skills）
3. 打包为任务配置
4. 试跑一次
5. 用户确认后注册到 `task-manifest.json`

### 启动调度器

```bash
# 定时调度（每分钟检查一次）
python3 dispatcher/dispatch.py

# 文件变化监控
node dispatcher/file_watch.js

# 手动触发单个任务
python3 dispatcher/dispatch.py run task-001

# 列出所有任务
python3 dispatcher/dispatch.py list
```

### 查看日志

```bash
# 查看某任务的执行历史
cat logs/task-001.log | python3 -m json.tool

# 最近一次执行
tail -1 logs/task-001.log | python3 -m json.tool
```

## 任务配置结构

```json
{
  "id": "task-001",
  "name": "每日报告",
  "environment": {
    "env_vars": ["LOG_PATH"],
    "tools": ["python3"],
    "files": ["./logs/"]
  },
  "task": {
    "instruction": "读取日志生成报告",
    "skills": ["self-improvement"],
    "timeout": 3600
  },
  "delivery": {
    "path": "./output/report.md",
    "log_path": "./logs/task-001.log"
  },
  "trigger": {
    "type": "schedule",
    "time": "09:00"
  },
  "status": "active"
}
```

## 操作规则

| 文件 | Create | Read | Update | Delete |
|------|--------|------|--------|--------|
| task-manifest.json | ✅ | ✅ | ✅ | ❌ |
| 执行日志 | ✅ append | ✅ | ❌ | ❌ |

需要停用任务？设 `status: "inactive"`，不删除。

## 与 OpenClaw 的区别

| OpenClaw | 本系统 |
|----------|--------|
| Gateway 监听端口 | 本地调度器轮询 |
| 任务信息存网关 | 任务配置存本地 JSON |
| 后台 daemon 常驻 | 触发脚本按需启动 |
| 日志可删改 | 日志 append-only |
| 任务可删除 | 任务只停用 |

## 文件结构

```
startup-compiler/
├── SKILL.md                    # 指令文件
├── README-HUMAN.md             # 本文件
├── DESIGN.md                   # 设计文档
├── dispatcher/
│   ├── dispatch.py             # 定时调度器
│   └── file_watch.js           # 文件变化调度器
└── assets/
    └── task-manifest-template.json  # 注册表模板
```

## License

MIT
