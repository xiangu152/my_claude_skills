---
name: startup-compiler
description: "Compile tasks into executable units with isolated environment, bundled skills, and immutable execution logs. Use when: (1) creating automated task execution, (2) compiling environment + logic + delivery into a task, (3) setting up scheduled or file-triggered tasks. Triggers on '编译任务', '打包任务', '自动执行', 'task compile'. NOT for: using gateways, webhooks, or background daemons."
---

# Startup Compiler

Compile tasks into self-contained execution units. Each task bundles its own environment, skills, and delivery method. Registered in `task-manifest.json`. Executed via local dispatchers. No gateway.

## Core Rules

1. **Task isolation** — Each task only knows its own config. No cross-task access.
2. **Registry immutability** — `task-manifest.json` supports create/read/update. No delete. Set `status: inactive` to retire.
3. **Log append-only** — Execution logs can only be appended and read. No modify, no delete.
4. **Compile before register** — Verify environment, test run, user confirms. Only then register.
5. **No gateway** — Local dispatchers only. No ports, no HTTP, no webhooks.

## File Structure

```
~/.claude/
├── task-manifest.json          # 任务注册表（CRUD 无 D）
├── dispatcher/
│   ├── _dispatched/            # 编译生成的任务指令文件
│   └── triggers/               # 编译生成的 trigger 函数
│       └── {task-id}_trigger.py
├── output/                     # 任务输出
└── logs/                       # 执行日志（append-only）
```

## Compilation Workflow

### Phase 1: Requirements

Ask user:
- What task to automate?
- Environment dependencies (env vars, tools, files)?
- Delivery method (output path, format)?
- Trigger condition（用自然语言描述调度需求，编译器自动生成 trigger 函数）
- Which skills to bundle?

### Phase 2: Environment Verification

```bash
# Check env vars
for var in $REQUIRED_VARS; do
  [ -z "${!var}" ] && echo "❌ $var not set" || echo "✓ $var set"
done

# Check tools
which python3 > /dev/null 2>&1 || echo "❌ python3 not found"

# Check files
[ -d "./logs/" ] || echo "❌ ./logs/ not found"

# Check skills
ls ~/.claude/skills/$SKILL/ > /dev/null 2>&1 || echo "❌ skill $SKILL not found"
```

All dependencies must pass before proceeding.

### Phase 3: Package Task

**3a.** 创建任务配置并添加到 `task-manifest.json`：

```json
{
  "id": "task-001",
  "name": "Daily Report",
  "version": "1.0",
  "compiled_at": "2026-04-05T19:30:00+08:00",
  "environment": {
    "env_vars": ["LOG_PATH"],
    "tools": ["python3"],
    "files": ["./logs/"]
  },
  "task": {
    "instruction": "Read ./logs/ today and generate report",
    "skills": ["self-improvement"],
    "timeout": 3600
  },
  "delivery": {
    "path": "~/.claude/output/daily-report.md",
    "format": "markdown",
    "log_path": "~/.claude/logs/task-001.log"
  },
  "trigger": {
    "type": "schedule",
    "time": "09:00",
    "eval": "~/.claude/dispatcher/triggers/task-001_trigger.py"
  },
  "status": "active",
  "run_count": 0,
  "last_run": null
}
```

**3b.** 根据用户自然语言描述的调度需求，生成 trigger 函数文件 `~/.claude/dispatcher/triggers/{task-id}_trigger.py`。

函数接口（所有 trigger 文件统一）：

```python
def should_dispatch(context: dict) -> bool:
    """
    context = {
        "now": datetime.datetime,    # 当前本地时间
        "today": datetime.date,      # 当前日期
        "last_run": str | None,      # 上次发派的 ISO 时间戳
        "run_count": int,            # 已发派次数
        "task_dir": str,             # ~/.claude 绝对路径
    }
    """
```

每个文件**必须**包含 `if __name__ == '__main__':` 测试块，可独立运行验证。

示例（每天 09:00 触发）：

```python
import datetime

def should_dispatch(context):
    now = context["now"]
    today = context["today"]
    last_run = context.get("last_run")

    # 每天 09:00 触发
    if now.strftime("%H:%M") != "09:00":
        return False

    # 今天已执行则跳过
    if last_run and last_run.startswith(today.isoformat()):
        return False

    return True

if __name__ == '__main__':
    import datetime
    ctx = {
        "now": datetime.datetime.now(),
        "today": datetime.date.today(),
        "last_run": None,
        "run_count": 0,
        "task_dir": "~/.claude",
    }
    print(f"should_dispatch = {should_dispatch(ctx)}")
```

### Phase 4: Test Run

1. **验证 trigger 函数**：独立运行 trigger 函数文件，确认 `if __name__ == '__main__'` 输出合理
2. **试跑任务**：通过 dispatcher 手动触发，验证输出和日志
3. User confirms test passed

### Phase 5: Register

Only after test passes:
1. Add task to `task-manifest.json` (create if new, update if exists)
2. Record `compiled_at` timestamp
3. Start dispatcher if not already running

## Dispatchers

### dispatch.py (Schedule)

```bash
# Start
python3 ~/.claude/dispatcher/dispatch.py

# Background
nohup python3 ~/.claude/dispatcher/dispatch.py &
```

每 60 秒轮询所有 active 任务，调用 `evaluate_trigger(task, context)` 判断是否发派。
- 有 `trigger.eval` 字段 → 调用编译生成的 Python trigger 函数
- 无 `trigger.eval` 字段 → 走旧版硬编码逻辑（向后兼容）

### file_watch.js (File Change)

```bash
# Start
node ~/.claude/dispatcher/file_watch.js
```

监控指定文件变化。文件变化后，先调用 trigger 函数二次判断（如果配置了 `trigger.eval`），满足条件才发派。

### Cross-Platform Support

| 功能 | macOS | Windows | Linux |
|------|-------|---------|-------|
| 终端弹窗 | AppleScript → Terminal | `start cmd /c` | gnome-terminal / xterm |
| 窗口关闭 | osascript close | `exit` | `exit` |
| 环境变量注入 | ~/.zshrc, ~/.bashrc, ~/.bash_profile, ~/.profile | 系统环境变量（不读 rc 文件） | ~/.bashrc, ~/.profile |
| 工具检测 | `which` | `where` | `which` |
| Python 命令 | `python3` | `python` | `python3` |
| HOME 目录 | `$HOME` | `%USERPROFILE%` | `$HOME` |

### How Dispatch Works

```
Dispatcher detects trigger
    ↓
Read task-manifest.json (this task only)
    ↓
Build prompt with task config embedded
    ↓
osascript opens new terminal
    ↓
Terminal runs: claude --print "<prompt>"
    ↓
Claude reads config from prompt
    ↓
Executes task
    ↓
Writes output to delivery.path
    ↓
Appends log to delivery.log_path
    ↓
Terminal exits
```

## Registry Rules (task-manifest.json)

| Operation | Allowed | Method |
|-----------|---------|--------|
| Create | ✅ | Add new task object to `tasks` array |
| Read | ✅ | Parse JSON, find by ID |
| Update | ✅ | Modify existing task object |
| Delete | ❌ | **Never**. Set `status: "inactive"` instead |

```python
def create_task(task):
    data = read_manifest()
    if any(t['id'] == task['id'] for t in data['tasks']):
        raise ValueError(f"Task {task['id']} already exists. Use update.")
    data['tasks'].append(task)
    write_manifest(data)

def update_task(task_id, updates):
    data = read_manifest()
    task = next((t for t in data['tasks'] if t['id'] == task_id), None)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    task.update(updates)
    write_manifest(data)
```

## Log Rules (Append-Only)

| Operation | Allowed |
|-----------|---------|
| Append | ✅ |
| Read | ✅ |
| Modify | ❌ |
| Delete | ❌ |

```python
def append_log(task_id, entry):
    log_file = f"logs/{task_id}.log"
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
```

Log format (JSONL, one entry per line):

```json
{"task_id":"task-001","run_id":"run-20260405-090000","timestamp":"2026-04-05T09:00:00+08:00","status":"success","output":"./output/daily-report.md","duration_seconds":45}
```

## Setup

### Initialize Directory Structure

```bash
mkdir -p dispatcher output logs .claude
echo '{"tasks": []}' > task-manifest.json
```

### Create CLAUDE.md Entry Point

```markdown
# Task Compiler

Every session start:
1. Read `task-manifest.json` for active tasks
2. Check dispatcher status
3. Report: N active tasks, M scheduled
```

## Tips

- Use meaningful task IDs: `daily-report`, `code-review`, `patent-draft`
- Keep `task-manifest.json` in version control
- Logs are append-only by design — use `logrotate` if they grow too large
- Test every task before registering
- Skills bundled at compile time — if a skill updates, recompile the task
