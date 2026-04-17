"""Hooks for data_pipeline workflow."""
from typing import Any


def on_clean_done(task_name: str, result: Any) -> None:
    print(f"[data_pipeline] {task_name} completed, result length: {len(str(result))}")


def on_export_done(task_name: str, result: Any) -> None:
    print(f"[data_pipeline] {task_name} completed, file saved")


HOOKS = {
    "clean": on_clean_done,
    "export": on_export_done,
}
