# Startup Compiler — 设计文档

## 命名约定

注册表文件改名，避免与 Node.js 框架混淆：

| 旧名 | 新名 |
|------|------|
| `nodes.json` | `task-manifest.json` |
| 节点 | 任务（task） |

## 核心架构

```
task-manifest.json（任务注册表）
├── task-001: 每日报表
├── task-002: 代码审查
└── task-003: 专利撰写
    ↓
dispatcher/（调度器）
├── dispatch.py      ← 检测触发条件，读取任务配置，启动终端
└── 其他调度逻辑由 Claude Code 处理
    ↓
终端执行
├── 接收任务配置（仅该任务的信息）
├── 执行任务
└── 写入日志（append-only）
```

## 任务注册表（task-manifest.json）

### 操作规则

| 操作 | 允许 | 说明 |
|------|------|------|
| 创建（create） | ✅ | 编译新任务后添加 |
| 读取（read） | ✅ | 触发器读取配置 |
| 更新（update） | ✅ | 修改任务配置 |
| 删除（delete） | ❌ | **绝对禁止**，审计留痕 |

如需停用任务，将 `status` 设为 `inactive`，不删除。

### 结构

```json
{
  "tasks": [
    {
      "id": "task-001",
      "name": "每日报表",
      "version": "1.0",
      "compiled_at": "2026-04-05T19:30:00+08:00",

      "environment": {
        "env_vars": ["LOG_PATH"],
        "tools": ["python3", "pandas"],
        "files": ["./logs/"]
      },

      "task": {
        "instruction": "读取 ./logs/ 下今天的日志，生成日报写入 output/daily-report.md",
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
  ]
}
```

## 编译流程

编译由 Claude Code 执行，不是触发器。

```
Phase 1: 需求分析
  ├── 用户描述任务
  ├── 确认环境依赖（env vars、tools、files）
  ├── 确认交付方式（输出路径、格式）
  ├── 确认触发条件（定时/文件变化/手动）
  └── 确认需要打包的 skills

Phase 2: 环境验证
  ├── 检查 env vars 是否设置
  ├── 检查 tools 是否安装
  ├── 检查 files 是否存在
  ├── 检查 skills 是否已安装
  └── 所有依赖必须满足才能继续

Phase 3: 打包
  ├── 将环境依赖写入 task.environment
  ├── 将任务指令写入 task.task
  ├── 将需要的 skills 列表写入 task.task.skills
  ├── 将交付路径写入 task.delivery
  └── 将触发条件写入 task.trigger

Phase 4: 试跑
  ├── 模拟触发条件
  ├── 用打包好的配置启动终端
  ├── Claude 读取配置并执行
  ├── 验证输出是否符合预期
  └── 用户确认试跑结果

Phase 5: 注册
  ├── 试跑通过后，将任务写入 task-manifest.json
  ├── 使用 create（如果新任务）或 update（如果已有同 ID）
  ├── 不能 delete
  └── 记录 compiled_at 时间戳
```

## 调度器（dispatcher）

调度器只做两件事：**检测触发条件** 和 **发派任务**。调度逻辑由 Claude Code 处理。

### dispatcher.py

```python
#!/usr/bin/env python3
"""调度器 — 检测触发条件，发派任务到终端"""

import json
import time
import subprocess
import datetime
import os

MANIFEST = 'task-manifest.json'

def load_manifest():
    with open(MANIFEST, 'r') as f:
        return json.load(f)['tasks']

def save_manifest(tasks):
    with open(MANIFEST, 'r') as f:
        data = json.load(f)
    data['tasks'] = tasks
    with open(MANIFEST, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_task_config(task):
    """只返回该任务的配置，不暴露其他任务信息"""
    return json.dumps(task, ensure_ascii=False)

def compile_dispatch_command(task):
    """将任务配置编译为 Claude 命令"""
    config = get_task_config(task)
    instruction = task['task']['instruction']
    skills = ', '.join(task['task'].get('skills', []))

    prompt = f"""你正在执行一个自动化任务。

任务配置：
```json
{config}
```

请按照以上配置执行任务：
1. 验证环境依赖
2. 执行: {instruction}
3. 结果写入: {task['delivery']['path']}
4. 将执行日志追加到: {task['delivery']['log_path']}
5. 完成后退出终端

如需使用的 skills: {skills}
"""

    return f'claude --permission-mode bypassPermissions --print "{prompt}"'

def dispatch(task):
    """打开终端，发派任务"""
    command = compile_dispatch_command(task)
    escaped = command.replace('"', '\\"')

    # macOS
    script = f'tell application "Terminal" to do script "{escaped}"'
    subprocess.run(['osascript', '-e', script])

def check_schedule(tasks):
    """检查定时触发"""
    now = datetime.datetime.now().strftime("%H:%M")
    today = datetime.date.today().isoformat()

    for task in tasks:
        if task['status'] != 'active':
            continue
        if task['trigger']['type'] != 'schedule':
            continue
        if task['trigger']['time'] != now:
            continue

        # 检查今天是否已执行
        last_run = task.get('last_run', '')
        if last_run and last_run.startswith(today):
            continue

        print(f"[{now}] 发派任务: {task['name']}")
        dispatch(task)

        # 更新状态
        task['last_run'] = datetime.datetime.now().isoformat()
        task['run_count'] = task.get('run_count', 0) + 1
        save_manifest(tasks)

def check_file_watch(tasks):
    """检查文件变化触发（由 file_watch.py 处理，这里仅读取配置）"""
    watch_tasks = [t for t in tasks if t['trigger']['type'] == 'file_watch' and t['status'] == 'active']
    return watch_tasks

if __name__ == '__main__':
    print("调度器运行中... (Ctrl+C 退出)")
    while True:
        tasks = load_manifest()
        check_schedule(tasks)
        time.sleep(60)
```

### dispatcher_file_watch.js

```javascript
#!/usr/bin/env node
/** 文件变化调度器 — 监控文件变化，发派任务 */

const fs = require('fs');
const { exec } = require('child_process');

const MANIFEST = 'task-manifest.json';

function loadTasks() {
    return JSON.parse(fs.readFileSync(MANIFEST, 'utf8')).tasks;
}

function getTaskConfig(task) {
    return JSON.stringify(task, null, 2);
}

function compileDispatchCommand(task) {
    const config = getTaskConfig(task);
    const instruction = task.task.instruction;
    const skills = (task.task.skills || []).join(', ');

    const prompt = `你正在执行一个自动化任务。任务配置：\n\`\`\`json\n${config}\n\`\`\`\n请执行：${instruction}\n结果写入：${task.delivery.path}\n日志追加到：${task.delivery.log_path}\nSkills：${skills}\n完成后退出。`;

    const escaped = prompt.replace(/"/g, '\\"').replace(/\n/g, '\\n');
    return `claude --permission-mode bypassPermissions --print "${escaped}"`;
}

function dispatch(task) {
    const command = compileDispatchCommand(task);
    const escaped = command.replace(/'/g, "'\\''");
    exec(`osascript -e 'tell application "Terminal" to do script "${escaped}"'`);

    // 更新 last_run
    const data = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
    const target = data.tasks.find(t => t.id === task.id);
    if (target) {
        target.last_run = new Date().toISOString();
        target.run_count = (target.run_count || 0) + 1;
        fs.writeFileSync(MANIFEST, JSON.stringify(data, null, 2));
    }
}

// 启动文件监控
const tasks = loadTasks();
const watchTasks = tasks.filter(t => t.status === 'active' && t.trigger?.type === 'file_watch');

watchTasks.forEach(task => {
    const watchFile = task.trigger.file;
    console.log(`监控: ${watchFile} → 任务: ${task.name}`);

    fs.watchFile(watchFile, { interval: 5000 }, (curr, prev) => {
        if (curr.mtime > prev.mtime) {
            console.log(`[${new Date().toISOString()}] 文件变化: ${watchFile}`);
            dispatch(task);
        }
    });
});

console.log('文件变化调度器运行中... (Ctrl+C 退出)');
```

## 日志系统

### 规则

| 操作 | 允许 | 说明 |
|------|------|------|
| 创建（append） | ✅ | 每次执行追加一条记录 |
| 读取（read） | ✅ | 查看执行历史 |
| 修改（update） | ❌ | **绝对禁止** |
| 删除（delete） | ❌ | **绝对禁止** |

### 日志格式

每个任务一个日志文件：`logs/{task-id}.log`

```jsonl
{"task_id":"task-001","run_id":"run-20260405-090000","timestamp":"2026-04-05T09:00:00+08:00","status":"success","output":"./output/daily-report.md","duration_seconds":45}
{"task_id":"task-001","run_id":"run-20260406-090000","timestamp":"2026-04-06T09:00:00+08:00","status":"success","output":"./output/daily-report.md","duration_seconds":52}
{"task_id":"task-001","run_id":"run-20260407-090000","timestamp":"2026-04-07T09:00:00+08:00","status":"failed","error":"LOG_PATH not set","duration_seconds":3}
```

### 日志写入（Claude 执行时）

```python
def append_log(task_id, result):
    """追加日志，不可修改已有记录"""
    import json
    from datetime import datetime

    log_entry = {
        "task_id": task_id,
        "run_id": f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "status": result['status'],
        "output": result.get('output'),
        "error": result.get('error'),
        "duration_seconds": result.get('duration'),
    }

    log_file = f"logs/{task_id}.log"

    # 追加模式，不可修改已有内容
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
```

### 日志查询

```bash
# 查看某任务的执行历史
cat logs/task-001.log | python3 -m json.tool

# 查看最近一次执行
tail -1 logs/task-001.log | python3 -m json.tool

# 统计成功/失败次数
cat logs/task-001.log | python3 -c "
import sys, json
success = sum(1 for line in sys.stdin if json.loads(line)['status'] == 'success')
print(f'Success: {success}')
"
```

## 执行流程（完整）

```
调度器检测到触发条件
    ↓
读取 task-manifest.json 中对应任务的配置
    ↓
编译发派命令（将任务配置内嵌到 prompt 中）
    ↓
osascript 打开新终端
    ↓
终端运行: claude --print "<包含任务配置的 prompt>"
    ↓
Claude 读取 prompt 中的任务配置
    ↓
验证环境依赖（env vars、tools、files）
    ↓
执行任务指令
    ↓
结果写入 delivery.path
    ↓
执行日志追加到 delivery.log_path（JSONL 格式）
    ↓
终端 exit，关闭
```

## 编译试跑流程（详细）

```
Phase 1: 需求分析
  用户: "每天 9 点读取 logs 生成日报"
  Claude: 确认需要:
    - env_vars: ["LOG_PATH"]
    - tools: ["python3"]
    - files: ["./logs/"]
    - delivery: "./output/daily-report.md"
    - trigger: schedule, 09:00
    - skills: []

Phase 2: 环境验证
  Claude 执行:
    - [ -z "$LOG_PATH" ] && echo "❌ 未设置"
    - which python3 || echo "❌ 未安装"
    - ls ./logs/ || echo "❌ 目录不存在"

Phase 3: 打包
  Claude 生成 task 配置 JSON

Phase 4: 试跑
  Claude 模拟一次执行:
    - 读取 ./logs/ 下今天的日志
    - 生成日报
    - 写入 ./output/daily-report.md
    - 用户确认输出正确

Phase 5: 注册
  Claude 将 task 写入 task-manifest.json
  启动 dispatcher.py
```

## 目录结构

```
项目/
├── task-manifest.json          # 任务注册表（只增改查，不删除）
├── dispatcher/
│   ├── dispatch.py             # 定时调度器
│   └── file_watch.js           # 文件变化调度器
├── output/                     # 任务输出
│   └── daily-report.md
├── logs/                       # 执行日志（append-only）
│   └── task-001.log
└── .claude/
    └── CLAUDE.md               # 启动指引
```

## 与 OpenClaw 的对比

| OpenClaw | 本系统 |
|----------|--------|
| `openclaw cron add` | 编译任务到 task-manifest.json |
| Gateway 监听 | 本地调度器轮询 |
| 任务信息存储在网关 | 任务配置存储在本地 JSON |
| Session 持久化 | 每次执行开新终端，执行完关闭 |
| 日志可删改 | 日志 append-only |
| 任务可删除 | 任务只停用（inactive），不删除 |
| 全局任务池 | 每个任务隔离，只知道自己配置 |
