"""
Task Orchestration - Subagent coordination with DAG-based task scheduling.

Usage:
    from task_orchestration import Task, create_task_core

    # Define tasks
    tasks = [
        Task(name="task_a", detail="Do part A", dependencies=[]),
        Task(name="task_b", detail="Do part B", dependencies=["task_a"]),
        Task(name="task_c", detail="Do part C", dependencies=["task_a"]),
        Task(name="task_d", detail="Do part D", dependencies=["task_b", "task_c"]),
    ]

    # Create and start core
    core = create_task_core([t.__dict__ for t in tasks])
    await core.start()

    # In your agent loop:
    # runnable = core.get_runnable()  # Returns ["task_a"]
    # After task_a completes, runnable = ["task_b", "task_c"]
"""

from .core import TaskCore, create_task_core, create_task_core_from_json, create_task_core_from_workflows, create_task_core_from_workflow_objects, create_task_core_from_workflow_folders
from .graph import CycleDetectedError, TaskGraph
from .hooks import HookQueue, HookRegistry
from .types import Task, TaskResult

__all__ = [
    "Task",
    "TaskResult",
    "TaskGraph",
    "TaskCore",
    "create_task_core",
    "create_task_core_from_json",
    "create_task_core_from_workflows",
    "create_task_core_from_workflow_objects",
    "create_task_core_from_workflow_folders",
    "HookRegistry",
    "HookQueue",
    "CycleDetectedError",
]
