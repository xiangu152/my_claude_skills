"""TaskGraph - Directed Acyclic Graph (DAG) for task dependencies."""
from collections import defaultdict
from typing import Any

from .types import Task


class CycleDetectedError(Exception):
    """Raised when task dependencies contain a cycle."""
    pass


class TaskGraph:
    """
    Directed Acyclic Graph for task scheduling.

    Manages task dependencies and computes which tasks are runnable
    (i.e., all their dependencies have completed).
    """

    def __init__(self, tasks: list[Task]):
        """
        Initialize the task graph.

        Args:
            tasks: List of Task definitions.

        Raises:
            CycleDetectedError: If dependencies form a cycle.
            ValueError: If a task references a non-existent dependency.
        """
        self.tasks: dict[str, Task] = {t.name: t for t in tasks}
        self._adjacency: dict[str, list[str]] = defaultdict(list)  # task -> dependents
        self._in_degree: dict[str, int] = defaultdict(int)
        self._build_graph(tasks)

    def _build_graph(self, tasks: list[Task]) -> None:
        """Build the DAG from task definitions."""
        # Initialize all tasks with 0 in-degree
        for task in tasks:
            self._in_degree[task.name] = 0

        # Build adjacency list and compute in-degrees
        for task in tasks:
            for dep in task.dependencies:
                if dep not in self.tasks:
                    raise ValueError(f"Task '{task.name}' depends on non-existent task '{dep}'")
                self._adjacency[dep].append(task.name)
                self._in_degree[task.name] += 1

        # Validate no cycles using Kahn's algorithm
        self._validate_dag()

    def _validate_dag(self) -> None:
        """Validate that the graph is acyclic using Kahn's algorithm."""
        queue = [name for name, degree in self._in_degree.items() if degree == 0]
        visited_count = 0

        temp_in_degree = self._in_degree.copy()
        while queue:
            node = queue.pop(0)
            visited_count += 1
            for neighbor in self._adjacency[node]:
                temp_in_degree[neighbor] -= 1
                if temp_in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(self.tasks):
            raise CycleDetectedError(
                f"Cycle detected in task dependencies. "
                f"Visited {visited_count} of {len(self.tasks)} tasks."
            )

    def get_runnable(self, completed: set[str]) -> list[str]:
        """
        Return tasks that are runnable (dependencies satisfied, not yet completed).

        Args:
            completed: Set of task names that have already completed.

        Returns:
            List of task names that can be run now.
        """
        runnable = []
        for task_name, task in self.tasks.items():
            if task_name in completed:
                continue
            # Check if all dependencies are satisfied
            if all(dep in completed for dep in task.dependencies):
                runnable.append(task_name)
        return runnable

    def is_complete(self, completed: set[str]) -> bool:
        """Check if all tasks have completed."""
        return len(completed) == len(self.tasks)

    def get_task(self, name: str) -> Task | None:
        """Get a task by name."""
        return self.tasks.get(name)

    def all_tasks(self) -> list[str]:
        """Return all task names in topological order."""
        # Kahn's algorithm for topological sort
        result = []
        queue = [name for name, degree in self._in_degree.items() if degree == 0]
        temp_in_degree = self._in_degree.copy()

        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in self._adjacency[node]:
                temp_in_degree[neighbor] -= 1
                if temp_in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result
