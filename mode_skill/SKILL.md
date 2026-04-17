---
name: task-orchestration
description: Use when coordinating multiple subagents with dependency relationships, parallel execution, or post-processing hooks. Triggers: subagent runs wrong order, no hook fired, don't know which tasks can run in parallel, need to create new workflow for a pipeline.
---

# Task Orchestration

## Overview

Coordinate multiple subagents using DAG-based dependency management. Tasks declare dependencies; TaskCore reports which are currently runnable and triggers hooks on completion.

## When to Use

- Multiple subagents with dependency order
- Tasks that can run in parallel but unsure which are safe
- Post-processing needed after each subagent finishes
- Subagents finish but nothing happens (no hook triggered)
- Main agent runs tasks in wrong order (dependency violation)
- Need to create a new workflow for a pipeline

## Directory Structure

```
tasks/workflows/
└── my_workflow/
    ├── tasks/
    │   ├── task1.md
    │   ├── task2.md
    │   └── task3.md
    ├── hooks.py
    └── workflow.py
```

## Quick Reference

| Operation | Location |
| --- | --- |
| Create task | `tasks/workflows/<name>/tasks/<task>.md` |
| Define dependencies | `tasks/workflows/<name>/workflow.py` |
| Define hooks | `tasks/workflows/<name>/hooks.py` |
| Load workflows | `create_task_core_from_workflow_folders()` |

## Using Workflow Folders

### 1. Create task md files

```markdown
# task_name
detail: Instructions for subagent
predo: prepare_data  # optional - auto-triggered before task runs
hook: on_task_done   # optional - triggered after task completes
```

### 2. Define workflow.py

```python
# Linear: "a,b,c" means a→b→c (b depends on a, c depends on b)
WORKFLOW = "fetch,clean,export"

# Parallel branches: ";" separates independent branches
# "fetch,clean;fetch,analyze" = two parallel chains starting from "fetch"

# Multi-dependency: "task:dep1,dep2" means task depends on both dep1 AND dep2
# "save:clean,analyze" = save depends on both clean AND analyze
WORKFLOW = "fetch,clean;fetch,analyze;save:clean,analyze"
```

### 3. Define hooks.py (optional)

```python
def prepare_data(task_name):
    """Predo - runs automatically before task becomes runnable."""
    print(f"Preparing data for {task_name}")

def on_clean_done(task_name, result):
    """Hook - runs async after task completes."""
    print(f"{task_name} done with result: {result}")

HOOKS = {
    "clean": on_clean_done,
}

PREDOS = {
    "clean": prepare_data,  # "clean" is the task name, not function name
}
```

### 4. Predo vs Hook

| Feature | Predo | Hook |
|---------|-------|------|
| When | Before task becomes runnable | After task completes |
| Trigger | Automatic when deps satisfied | Automatic after POST /complete |
| Use case | Setup, validation, preparation | Post-processing, side effects |
| Signature | `(task_name) -> None` | `(task_name, result) -> None` |

### 5. Load and use

```python
from task_orchestration import create_task_core_from_workflow_folders

core = create_task_core_from_workflow_folders(
    ["my_workflow"],
    base_path="tasks/workflows"
)
await core.start()
```

### 6. Main Agent Coordination Loop

Main agent only polls `/runnable` and launches subagents with task names.
Subagents fetch their own task details.

```python
while not core.is_complete():
    runnable = core.get_runnable()  # GET /runnable
    for task_name in runnable:
        # Launch subagent with ONLY the task name - subagent fetches detail itself
        launch_subagent(task_name)
    time.sleep(1)
```

**Flow**:
1. Server starts → predoes auto-trigger for tasks with no dependencies
2. Poll `/runnable` → get currently runnable task names
3. Launch subagent for each task name (subagent fetches detail via GET /task/{name})
4. Subagents execute and POST /complete/{name}
5. Hooks run async in background
6. After task's hook finishes → dependent tasks' predoes auto-trigger
7. After predo finishes → task becomes runnable
8. Poll `/runnable` again → new tasks appear
9. Repeat until all complete

## Subagent Protocol

Main agent launches subagent with ONLY a task name. Subagent handles everything else:

```python
# Subagent code - main agent only gives task_name
detail = requests.get(f"{core.base_url}/task/{task_name}").json()["detail"]
# ... do work based on detail ...
# POST returns immediately, hook runs in background
response = requests.post(f"{core.base_url}/complete/{task_name}", json={"result": the_result})
# Subagent's work is done
```

**Key concept - Truly Complete**: A task is "truly complete" only when:
- Subagent reported completion (POST succeeded), AND
- Hook finished executing (if task has a hook)

**Key concept - Runnable**: A task becomes "runnable" when:
- All dependencies are truly complete, AND
- Predo finished executing (if task has a predo)

`/runnable` won't show dependent tasks until their dependencies' hooks AND predoes finish.

**Critical**: Subagent must call POST `/complete/{name}` or:
- Hooks will NOT fire
- DAG will NOT update
- Workflow will stall

## Common Errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| `/runnable` returns empty but tasks incomplete | Dependencies not satisfied yet | Wait, query again |
| Hook never fires | Subagent didn't POST `/complete/{name}` | Must call completion API |
| `CycleDetectedError` | Circular dependency in workflow.py | Check WORKFLOW chains |
| `Connection refused` on 8765 | TaskCore not started | `await core.start()` first |
| 400 Bad Request on GET `/task/{name}` | Task already completed | Check `/runnable` first |

## Red Lines — Stop and Restart

- **Subagent finished but no POST to `/complete/{name}`?** → Protocol violated. Hooks won't fire. Workflow stalls.
- **Main agent running tasks without calling `/runnable`?** → Will violate dependencies. Always query `/runnable` first.
- **Manually ordering tasks instead of using DAG output?** → Wrong. DAG determines order.
- **Launching multiple subagents for same task?** → Only launch ONE per task. Multiple POST `/complete/{name}` causes 400 error.

## Loopholes

| Rationalization | Reality |
| --- | --- |
| "I'll just run all tasks in parallel" | Dependent tasks will fail (run before prerequisites) |
| "Task completed silently, no need to POST" | Hooks never fire, graph never updates, workflow stalls |
| "Dependencies are optional" | No — DAG enforces constraints strictly |
| "I can skip the detail and guess" | Wrong — `detail` contains actual instructions |
| "Task order in workflow.py is execution order" | No — `;` creates parallel branches, DAG resolves order |
