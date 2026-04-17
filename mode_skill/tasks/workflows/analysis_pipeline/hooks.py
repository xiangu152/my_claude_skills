"""Hooks for analysis_pipeline workflow."""
from typing import Any


def on_report_done(task_name: str, result: Any) -> None:
    print(f"[analysis_pipeline] {task_name} completed")


HOOKS = {
    "report": on_report_done,
}
