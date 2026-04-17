# Task 工作流操作指南

## 目录结构

```text
tasks/workflows/
└── my_workflow/
    ├── tasks/
    │   ├── task1.md
    │   ├── task2.md
    │   └── task3.md
    ├── hooks.py    # 钩子函数（可选）
    └── workflow.py # 工作流定义
```

## task md 文件格式

```markdown
# task_name
detail: 给 subagent 的指令
hook: hook_function_name  # 可选
```

## workflow.py 格式

```python
WORKFLOW = "fetch,clean,export"
```

### 语法

| 格式 | 含义 |
| --- | --- |
| `a,b,c` | 线性链：b 依赖 a，c 依赖 b |
| `task:dep1,dep2,dep3` | 多依赖：task 同时依赖多个任务 |

### 示例

```python
# 线性工作流
WORKFLOW = "fetch,clean,export"

# 多分支工作流
WORKFLOW = "fetch,clean;fetch,analyze;fetch,export;save:clean,analyze,export"
```

解释：

- `fetch,clean` → fetch → clean
- `fetch,analyze` → fetch → analyze
- `fetch,export` → fetch → export
- `save:clean,analyze,export` → save 同时依赖 clean, analyze, export

## hooks.py 格式

```python
def on_task_done(task_name, result):
    print(f"{task_name} done")

HOOKS = {
    "task_name": on_task_done,
}
```

## 使用方式

```python
from task_orchestration import create_task_core_from_workflow_folders

core = create_task_core_from_workflow_folders(
    ["my_workflow"],
    base_path="tasks/workflows"
)
await core.start()
```

## 快速参考

| 操作 | 位置 |
| --- | --- |
| 定义任务 | `tasks/<workflow>/tasks/*.md` |
| 定义依赖 | `tasks/<workflow>/workflow.py` 的 WORKFLOW |
| 定义钩子 | `tasks/<workflow>/hooks.py` 的 HOOKS |
| 加载工作流 | `create_task_core_from_workflow_folders()` |
