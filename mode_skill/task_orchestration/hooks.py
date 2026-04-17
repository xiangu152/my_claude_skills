"""Hook registration and synchronous execution for task completion."""
import asyncio
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class HookRegistry:
    """
    Registry for task completion hooks.

    Hooks are synchronous functions that are called when a task completes.
    They are executed sequentially in registration order.
    """

    def __init__(self):
        self._hooks: dict[str, list[Callable[[str, Any], None]]] = {}

    def register(self, task_name: str, hook: Callable[[str, Any], None]) -> None:
        """
        Register a hook for a specific task.

        Args:
            task_name: Name of the task to hook into.
            hook: Function to call when task completes.
                  Signature: (task_name: str, result: Any) -> None
        """
        if task_name not in self._hooks:
            self._hooks[task_name] = []
        self._hooks[task_name].append(hook)
        logger.debug(f"Registered hook for task '{task_name}', total hooks: {len(self._hooks[task_name])}")

    def trigger(self, task_name: str, result: Any) -> None:
        """
        Trigger all hooks for a completed task.

        Hooks are executed synchronously in registration order.
        If a hook raises an exception, subsequent hooks are still called.

        Args:
            task_name: Name of the completed task.
            result: Result from the task.
        """
        hooks = self._hooks.get(task_name, [])
        for hook in hooks:
            try:
                hook(task_name, result)
            except Exception as e:
                logger.error(f"Hook for task '{task_name}' raised exception: {e}", exc_info=True)

    def unregister(self, task_name: str, hook: Callable[[str, Any], None]) -> bool:
        """
        Remove a specific hook.

        Args:
            task_name: Name of the task.
            hook: The hook function to remove.

        Returns:
            True if the hook was found and removed, False otherwise.
        """
        if task_name not in self._hooks:
            return False
        try:
            self._hooks[task_name].remove(hook)
            return True
        except ValueError:
            return False

    def clear(self, task_name: str | None = None) -> None:
        """
        Clear hooks.

        Args:
            task_name: If provided, clear hooks for only this task.
                       If None, clear all hooks.
        """
        if task_name is None:
            self._hooks.clear()
        else:
            self._hooks.pop(task_name, None)


class HookQueue:
    """
    Asynchronous queue for processing hook executions.

    This allows task completion reports to be queued and processed
    asynchronously without blocking the FastAPI request handler.
    """

    def __init__(self):
        self._queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()
        self._running = False
        self._task: asyncio.Task | None = None
        self._on_complete: callable | None = None  # Callback when hook finishes

    def set_complete_callback(self, callback: callable) -> None:
        """Set callback to invoke when a hook finishes execution."""
        self._on_complete = callback

    async def put(self, task_name: str, result: Any) -> None:
        """Add a task completion to the queue."""
        await self._queue.put((task_name, result))

    async def _process(self, registry: HookRegistry) -> None:
        """Process queue items and trigger hooks synchronously."""
        while self._running:
            try:
                task_name, result = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                registry.trigger(task_name, result)
                # Notify callback after hook completes
                if self._on_complete:
                    self._on_complete(task_name)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing hook queue: {e}", exc_info=True)

    async def start(self, registry: HookRegistry) -> None:
        """Start the queue processor."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._process(registry))

    async def stop(self) -> None:
        """Stop the queue processor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def pending_count(self) -> int:
        """Return the number of items waiting in the queue."""
        return self._queue.qsize()


class PredoQueue:
    """
    Asynchronous queue for processing predo executions.

    Predo is triggered automatically when dependencies are satisfied,
    and must complete before the task becomes runnable.
    """

    def __init__(self):
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._running = False
        self._task: asyncio.Task | None = None
        self._on_complete: callable | None = None
        self._predo_funcs: dict[str, callable] = {}

    def set_complete_callback(self, callback: callable) -> None:
        """Set callback to invoke when a predo finishes."""
        self._on_complete = callback

    def register_predo(self, task_name: str, predo_func: callable) -> None:
        """Register a predo function for a task."""
        self._predo_funcs[task_name] = predo_func

    async def put(self, task_name: str) -> None:
        """Add a task to the predo queue."""
        await self._queue.put(task_name)

    async def _process(self) -> None:
        """Process queue items and execute predoes."""
        while self._running:
            try:
                task_name = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                predo_func = self._predo_funcs.get(task_name)
                if predo_func:
                    logger.info(f"Executing predo for '{task_name}'")
                    predo_func(task_name)
                if self._on_complete:
                    self._on_complete(task_name)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing predo queue: {e}", exc_info=True)

    async def start(self) -> None:
        """Start the queue processor."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._process())

    async def stop(self) -> None:
        """Stop the queue processor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def pending_count(self) -> int:
        """Return the number of items waiting in the queue."""
        return self._queue.qsize()
