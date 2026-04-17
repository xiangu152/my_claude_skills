"""Hooks for multi_branch workflow."""
from typing import Any


def on_save_done(task_name: str, result: Any) -> None:
    print(f"[multi_branch] {task_name} completed, all branches merged")


HOOKS = {
    "save": on_save_done,
}
