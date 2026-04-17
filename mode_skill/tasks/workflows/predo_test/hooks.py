"""Hooks for predo test workflow."""
import time


def pre_b(task_name):
    """Predo for b - adds delay to verify predo blocks task execution."""
    print(f"[Predo] {task_name} starting, will sleep 2 seconds...")
    time.sleep(2)
    print(f"[Predo] {task_name} finished")


PREDOS = {
    "b": pre_b,
}