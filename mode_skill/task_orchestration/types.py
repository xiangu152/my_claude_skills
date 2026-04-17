"""Task data structures for task orchestration."""
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Task:
    """
    Task definition for subagent execution.

    Attributes:
        name: Unique task identifier (what subagent receives).
        detail: Long string returned to subagent via GET /task/{name}.
        dependencies: List of task names that must complete before this task.
        predo: Optional function triggered automatically when dependencies are satisfied.
               Task becomes runnable only after predo completes.
               Signature: (task_name: str) -> None
        hook: Optional callback function called when task completes.
               Signature: (task_name: str, result: Any) -> None
    """
    name: str
    detail: str
    dependencies: list[str] = field(default_factory=list)
    predo: Callable[[str], None] | None = None
    hook: Callable[[str, Any], None] | None = None


@dataclass
class TaskResult:
    """Result from a completed task."""
    task_name: str
    result: Any
    completed_at: float  # timestamp
