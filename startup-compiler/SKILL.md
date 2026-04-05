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
项目/
├── task-manifest.json          # 任务注册表（CRUD 无 D）
├── dispatcher/
│   ├── dispatch.py             # 定时调度器
│   └── file_watch.js           # 文件变化调度器
├── output/                     # 任务输出
├── logs/                       # 执行日志（append-only）
└── .claude/
    └── CLAUDE.md               # 启动指引
```

## Compilation Workflow

### Phase 1: Requirements

Ask user:
- What task to automate?
- Environment dependencies (env vars, tools, files)?
- Delivery method (output path, format)?
- Trigger condition (schedule / file_watch / manual)?
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

Create task config and add to `task-manifest.json`:

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
    "path": "./output/daily-report.md",
    "format": "markdown",
    "log_path": "./logs/task-001.log"
  },
  "trigger": {
    "type": "schedule",
    "time": "09:00"
  },
  "status": "active",
  "run_count": 0,
  "last_run": null
}
```

### Phase 4: Test Run

Simulate execution:
1. Run dispatcher manually with this task
2. Verify output matches expected
3. Verify log entry is correct
4. User confirms test passed

### Phase 5: Register

Only after test passes:
1. Add task to `task-manifest.json` (create if new, update if exists)
2. Record `compiled_at` timestamp
3. Start dispatcher if not already running

## Dispatchers

### dispatch.py (Schedule)

```bash
# Start
python3 dispatcher/dispatch.py

# Background
nohup python3 dispatcher/dispatch.py &
```

Checks every 60 seconds. When time matches trigger, dispatches task to terminal.

### file_watch.js (File Change)

```bash
# Start
node dispatcher/file_watch.js
```

Watches specified files via `fs.watchFile`. On change, dispatches task.

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
