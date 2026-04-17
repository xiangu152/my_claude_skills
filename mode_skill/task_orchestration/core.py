"""TaskCore FastAPI service for task orchestration."""
import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from .graph import TaskGraph
from .hooks import HookQueue, HookRegistry, PredoQueue
from .types import Task, TaskResult

logger = logging.getLogger(__name__)


class TaskDetailResponse(BaseModel):
    """Response model for GET /task/{name}."""
    name: str
    detail: str


class CompletionRequest(BaseModel):
    """Request body for POST /complete/{name}."""
    result: Any


class CompletionResponse(BaseModel):
    """Response model for POST /complete/{name}."""
    task_name: str
    success: bool
    message: str


class RunnableResponse(BaseModel):
    """Response model for GET /runnable."""
    runnable: list[str]
    completed: list[str]
    pending: list[str]


class TaskCore:
    """
    Task orchestration core service.

    This class manages task definitions, dependency graphs,
    hook execution, and provides the FastAPI interface for subagents.
    """

    def __init__(self, tasks: list[Task], host: str = "127.0.0.1", port: int = 8765):
        """
        Initialize TaskCore.

        Args:
            tasks: List of task definitions.
            host: Host to bind the FastAPI server to.
            port: Port to bind the FastAPI server to.
        """
        self.host = host
        self.port = port
        self._graph = TaskGraph(tasks)
        self._completed: set[str] = set()
        self._results: dict[str, TaskResult] = {}
        self._hook_registry = HookRegistry()
        self._hook_queue = HookQueue()
        self._hooks_completed: set[str] = set()  # Track hook completion
        self._predo_completed: set[str] = set()  # Track predo completion
        self._predo_queue = PredoQueue()  # Queue for predo execution
        self._server_task: asyncio.Task | None = None
        self._app = self._create_app()
        self._results_lock = asyncio.Lock()

        # Auto-register hooks and predoes from task definitions
        for task in tasks:
            if task.hook is not None:
                self._hook_registry.register(task.name, task.hook)
            if task.predo is not None:
                self._predo_queue.register_predo(task.name, task.predo)

    def _on_hook_complete(self, task_name: str) -> None:
        """Callback when a hook finishes execution. Triggers dependent tasks' predoes."""
        self._hooks_completed.add(task_name)
        logger.info(f"Hook for '{task_name}' completed")
        # Trigger predoes for tasks that depend on this one
        self._trigger_pending_predoes()

    def _trigger_pending_predoes(self) -> None:
        """Trigger predoes for tasks whose dependencies are all satisfied."""
        truly_done = self._get_truly_completed()
        for task_name, task in self._graph.tasks.items():
            # Skip if already triggered
            if task_name in self._predo_completed:
                continue
            # Skip if no predo
            if task.predo is None:
                self._predo_completed.add(task_name)
                continue
            # Skip if dependencies not satisfied
            if not all(dep in truly_done for dep in task.dependencies):
                continue
            # Trigger predo
            logger.info(f"Triggering predo for '{task_name}'")
            asyncio.create_task(self._predo_queue.put(task_name))

    def _on_predo_complete(self, task_name: str) -> None:
        """Callback when a predo finishes execution."""
        self._predo_completed.add(task_name)
        logger.info(f"Predo for '{task_name}' completed")

    def _get_truly_completed(self) -> set[str]:
        """Get set of tasks that are truly done (completed + hook finished).

        A task is truly complete when:
        - It's in _completed (subagent reported), AND
        - Either it has no hook registered, OR its hook has finished
        """
        truly_done = set()
        for task_name in self._completed:
            task = self._graph.get_task(task_name)
            if task is None:
                continue
            # No hook = immediately done
            if task.hook is None:
                truly_done.add(task_name)
            # Has hook but not finished = not done yet
            elif task_name not in self._hooks_completed:
                continue
            # Hook finished = done
            else:
                truly_done.add(task_name)
        return truly_done

    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info("TaskCore starting...")
            # Set callbacks and start queues
            self._hook_queue.set_complete_callback(self._on_hook_complete)
            await self._hook_queue.start(self._hook_registry)
            self._predo_queue.set_complete_callback(self._on_predo_complete)
            await self._predo_queue.start()
            # Trigger initial predoes (tasks with no dependencies)
            self._trigger_pending_predoes()
            yield
            # Shutdown
            logger.info("TaskCore shutting down...")
            await self._hook_queue.stop()
            await self._predo_queue.stop()

        app = FastAPI(
            title="TaskCore",
            description="Task orchestration service for subagent coordination",
            version="1.0.0",
            lifespan=lifespan,
        )

        @app.get("/task/{name}", response_model=TaskDetailResponse)
        async def get_task_detail(name: str) -> TaskDetailResponse:
            """Get task details by name. Subagents call this to get their work."""
            task = self._graph.get_task(name)
            if task is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task '{name}' not found"
                )
            if name in self._completed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Task '{name}' has already completed"
                )
            return TaskDetailResponse(name=task.name, detail=task.detail)

        @app.post("/complete/{name}", response_model=CompletionResponse)
        async def report_completion(name: str, body: CompletionRequest) -> CompletionResponse:
            """Report task completion. Triggers hook if registered."""
            task = self._graph.get_task(name)
            if task is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task '{name}' not found"
                )
            if name in self._completed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Task '{name}' has already completed"
                )

            # Record completion
            async with self._results_lock:
                self._completed.add(name)
                self._results[name] = TaskResult(
                    task_name=name,
                    result=body.result,
                    completed_at=time.time()
                )

            # Queue hook for async execution (non-blocking)
            await self._hook_queue.put(name, body.result)

            logger.info(f"Task '{name}' completed, hook queued")
            return CompletionResponse(
                task_name=name,
                success=True,
                message="Task completed, hook triggered"
            )

        @app.get("/runnable", response_model=RunnableResponse)
        async def get_runnable() -> RunnableResponse:
            """Get list of tasks that are currently runnable.

            A task is runnable when:
            1. All dependencies are truly complete (completed + hook finished), AND
            2. Either it has no predo, OR its predo has finished
            """
            truly_done = self._get_truly_completed()
            # Filter: only tasks with satisfied predoes are runnable
            runnable = []
            for task_name in self._graph.get_runnable(truly_done):
                task = self._graph.get_task(task_name)
                if task and (task.predo is None or task_name in self._predo_completed):
                    runnable.append(task_name)
            all_tasks = set(self._graph.tasks.keys())
            pending = list(all_tasks - set(runnable) - truly_done)
            return RunnableResponse(
                runnable=runnable,
                completed=list(truly_done),
                pending=pending
            )

        @app.get("/status")
        async def get_status() -> dict:
            """Get overall status of all tasks."""
            truly_done = self._get_truly_completed()
            return {
                "total": len(self._graph.tasks),
                "completed": len(self._completed),
                "truly_completed": len(truly_done),
                "pending": len(self._graph.tasks) - len(truly_done),
                "is_complete": self._graph.is_complete(truly_done),
                "runnable": self._graph.get_runnable(truly_done),
                "hook_queue_size": self._hook_queue.pending_count(),
                "predo_queue_size": self._predo_queue.pending_count(),
            }

        @app.get("/result/{name}")
        async def get_result(name: str) -> dict:
            """Get the result of a completed task."""
            async with self._results_lock:
                if name not in self._results:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No result found for task '{name}'"
                    )
                result = self._results[name]
            return {
                "task_name": result.task_name,
                "result": result.result,
                "completed_at": result.completed_at,
            }

        return app

    async def start(self) -> None:
        """Start the FastAPI server."""
        import uvicorn
        config = uvicorn.Config(
            self._app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(server.serve())
        logger.info(f"TaskCore server started at http://{self.host}:{self.port}")

    async def wait_until_complete(self) -> None:
        """Wait until all tasks are complete."""
        while not self._graph.is_complete(self._completed):
            await asyncio.sleep(0.5)

    def register_hook(self, task_name: str, hook: callable) -> None:
        """Register a hook for a task."""
        self._hook_registry.register(task_name, hook)

    def get_runnable(self) -> list[str]:
        """Get list of currently runnable tasks (synchronous)."""
        return self._graph.get_runnable(self._completed)

    def is_complete(self) -> bool:
        """Check if all tasks are complete."""
        return self._graph.is_complete(self._completed)

    @property
    def base_url(self) -> str:
        """Get the base URL of the server."""
        return f"http://{self.host}:{self.port}"


def create_task_core(
    task_definitions: list[dict],
    host: str = "127.0.0.1",
    port: int = 8765,
) -> TaskCore:
    """
    Factory function to create a TaskCore from task definitions.

    Args:
        task_definitions: List of dicts with keys: name, detail, dependencies, hook.
        host: Server host.
        port: Server port.

    Returns:
        Configured TaskCore instance.
    """
    tasks = []
    for td in task_definitions:
        tasks.append(Task(
            name=td["name"],
            detail=td["detail"],
            dependencies=td.get("dependencies", []),
            hook=td.get("hook"),
        ))
    return TaskCore(tasks=tasks, host=host, port=port)


def create_task_core_from_json(
    json_path: str,
    hook_registry: dict[str, callable] | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> TaskCore:
    """
    Factory function to create a TaskCore from a JSON file.

    JSON format:
    {
        "tasks": {
            "task_name": {
                "detail": "...",
                "dependencies": [],
                "hook": null
            }
        },
        "workflows": "task1,task2;task3,task4"
    }

    Workflows are separated by `;`. Tasks within each workflow are separated by `,`.
    The workflow chain implies dependencies: task2 depends on task1, etc.

    Args:
        json_path: Path to the JSON file.
        hook_registry: Dict mapping hook names to functions.
        host: Server host.
        port: Server port.

    Returns:
        Configured TaskCore instance.
    """
    import json

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tasks_dict = data.get("tasks", {})
    workflows_str = data.get("workflows", "")

    # Build task list with merged dependencies
    # Track dependencies from workflows
    workflow_deps: dict[str, set[str]] = {}

    if workflows_str:
        for chain in workflows_str.split(";"):
            chain = chain.strip()
            if not chain:
                continue
            task_names = [t.strip() for t in chain.split(",")]
            for i, task_name in enumerate(task_names):
                if task_name not in workflow_deps:
                    workflow_deps[task_name] = set()
                if i > 0:
                    workflow_deps[task_name].add(task_names[i - 1])

    # Create tasks with merged dependencies (task definition + workflow chain)
    tasks = []
    for task_name, task_def in tasks_dict.items():
        deps = set(task_def.get("dependencies", []))
        if task_name in workflow_deps:
            deps.update(workflow_deps[task_name])

        hook_name = task_def.get("hook")
        hook_func = None
        if hook_name and hook_registry:
            hook_func = hook_registry.get(hook_name)

        tasks.append(Task(
            name=task_name,
            detail=task_def["detail"],
            dependencies=list(deps),
            hook=hook_func,
        ))

    return TaskCore(tasks=tasks, host=host, port=port)


def _parse_task_md(md_content: str) -> dict:
    """Parse a task md file into a dict."""
    lines = md_content.strip().split("\n")
    result = {
        "name": "",
        "detail": "",
        "dependencies": [],
        "hook": None,
    }

    current_field = None
    field_content = []

    for line in lines:
        line_stripped = line.strip()

        # First line with # is the task name
        if line_stripped.startswith("#"):
            result["name"] = line_stripped.lstrip("#").strip()
            continue

        if not line_stripped:
            continue

        # Check if line starts with a field marker
        if line_stripped.startswith("detail:"):
            if current_field == "detail":
                result["detail"] = "\n".join(field_content).strip()
            elif current_field == "dependencies" and field_content:
                deps = field_content[0].strip()
                if deps:
                    result["dependencies"] = [d.strip() for d in deps.split(",")]
            elif current_field == "hook" and field_content:
                hook_name = field_content[0].strip()
                if hook_name:
                    result["hook"] = hook_name
            current_field = "detail"
            content = line_stripped[len("detail:"):].strip()
            field_content = [content] if content else []
        elif line_stripped.startswith("dependencies:"):
            if current_field == "detail":
                result["detail"] = "\n".join(field_content).strip()
            elif current_field == "dependencies" and field_content:
                deps = field_content[0].strip()
                if deps:
                    result["dependencies"] = [d.strip() for d in deps.split(",")]
            elif current_field == "hook" and field_content:
                hook_name = field_content[0].strip()
                if hook_name:
                    result["hook"] = hook_name
            current_field = "dependencies"
            content = line_stripped[len("dependencies:"):].strip()
            field_content = [content] if content else []
        elif line_stripped.startswith("hook:"):
            if current_field == "detail":
                result["detail"] = "\n".join(field_content).strip()
            elif current_field == "dependencies" and field_content:
                deps = field_content[0].strip()
                if deps:
                    result["dependencies"] = [d.strip() for d in deps.split(",")]
            elif current_field == "hook" and field_content:
                hook_name = field_content[0].strip()
                if hook_name:
                    result["hook"] = hook_name
            current_field = "hook"
            content = line_stripped[len("hook:"):].strip()
            field_content = [content] if content else []
        else:
            # Continuation of previous field
            field_content.append(line_stripped)

    # Save last field
    if current_field == "detail":
        result["detail"] = "\n".join(field_content).strip()
    elif current_field == "dependencies" and field_content:
        deps = field_content[0].strip()
        if deps:
            result["dependencies"] = [d.strip() for d in deps.split(",")]
    elif current_field == "hook" and field_content:
        hook_name = field_content[0].strip()
        if hook_name:
            result["hook"] = hook_name

    return result


def create_task_core_from_workflows(
    tasks_dir: str,
    task_graph_filename: str = "task_graph.json",
    hook_registry: dict[str, callable] | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> TaskCore:
    """
    Factory function to create a TaskCore from workflow folders with task md files.

    Directory structure:
        tasks_dir/
        ├── task_graph.json          # Workflow definitions
        └── workflows/
            ├── workflow_a/
            │   ├── task1.md
            │   └── task2.md
            └── workflow_b/
                └── task3.md

    task_graph.json format:
    {
        "workflows": {
            "workflow_a": "task1,task2",
            "workflow_b": "task3"
        }
    }

    Task md file format:
        # task_name
        detail: 详细指令...
        dependencies: task1, task2
        hook: hook_function_name

    Args:
        tasks_dir: Path to the tasks directory containing workflows/ subfolder.
        task_graph_filename: Name of the task graph JSON file.
        hook_registry: Dict mapping hook names to functions.
        host: Server host.
        port: Server port.

    Returns:
        Configured TaskCore instance.
    """
    import json
    import os

    tasks_dir = os.path.abspath(tasks_dir)
    task_graph_path = os.path.join(tasks_dir, task_graph_filename)

    with open(task_graph_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    workflows = data.get("workflows", {})

    # Load all task md files
    tasks_definitions: dict[str, dict] = {}
    workflows_dir = os.path.join(tasks_dir, "workflows")

    for workflow_name, task_chain in workflows.items():
        workflow_path = os.path.join(workflows_dir, workflow_name)
        if not os.path.isdir(workflow_path):
            raise ValueError(f"Workflow folder not found: {workflow_path}")

        # Read all .md files in workflow folder
        for filename in os.listdir(workflow_path):
            if not filename.endswith(".md"):
                continue
            md_path = os.path.join(workflow_path, filename)
            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()

            task_def = _parse_task_md(md_content)
            task_name = task_def.get("name") or os.path.splitext(filename)[0]
            tasks_definitions[task_name] = task_def

    # Build dependencies from workflow chains
    workflow_deps: dict[str, set[str]] = {}

    for workflow_name, task_chain in workflows.items():
        # Split by ';' first to get individual chains, then by ','
        chains = [chain.strip() for chain in task_chain.split(";")]
        for chain in chains:
            if not chain:
                continue
            task_names = [t.strip() for t in chain.split(",")]
            for i, task_name in enumerate(task_names):
                if task_name not in workflow_deps:
                    workflow_deps[task_name] = set()
                if i > 0:
                    workflow_deps[task_name].add(task_names[i - 1])

    # Create Task objects with merged dependencies
    tasks = []
    for task_name, task_def in tasks_definitions.items():
        deps = set(task_def.get("dependencies", []))
        if task_name in workflow_deps:
            deps.update(workflow_deps[task_name])

        hook_name = task_def.get("hook")
        hook_func = None
        if hook_name and hook_registry:
            hook_func = hook_registry.get(hook_name)

        tasks.append(Task(
            name=task_name,
            detail=task_def.get("detail", ""),
            dependencies=list(deps),
            hook=hook_func,
        ))

    return TaskCore(tasks=tasks, host=host, port=port)


def create_task_core_from_workflow_objects(
    workflows: list[Any],
    host: str = "127.0.0.1",
    port: int = 8765,
) -> TaskCore:
    """
    Create TaskCore from workflow template objects or names.

    Accepts either:
    - WorkflowTemplate instances
    - String workflow names (will be compiled via factory)

    Args:
        workflows: List of WorkflowTemplate instances or workflow name strings.
        host: Server host.
        port: Server port.

    Returns:
        Configured TaskCore instance.
    """
    from tasks.hooks import WorkflowFactory

    # Collect all tasks and build hook registry
    all_tasks = []
    hook_registry: dict[str, callable] = {}

    for workflow in workflows:
        # If string, compile via factory
        if isinstance(workflow, str):
            workflow = WorkflowFactory.create(workflow)

        for task_def in workflow.get_tasks():
            task_name = task_def["name"]
            all_tasks.append(Task(
                name=task_name,
                detail=task_def["detail"],
                dependencies=task_def.get("dependencies", []),
                hook=None,  # Hooks registered separately
            ))
            # Register hook if present
            hook_name = task_def.get("hook")
            if hook_name:
                hooks = workflow.get_hooks()
                if hook_name in hooks:
                    hook_registry[task_name] = hooks[hook_name]

    core = TaskCore(tasks=all_tasks, host=host, port=port)

    # Register all hooks
    for task_name, hook_func in hook_registry.items():
        core.register_hook(task_name, hook_func)

    return core


def create_task_core_from_workflow_folders(
    workflow_folders: list[str],
    workflow_names: list[str] | None = None,
    base_path: str = "tasks/workflows",
    host: str = "127.0.0.1",
    port: int = 8765,
) -> TaskCore:
    """
    Create TaskCore from workflow folders.

    Each folder is read and a DynamicWorkflow is created automatically.
    Folder structure:
        base_path/
        ├── workflow_name/
        │   ├── tasks/
        │   │   ├── task1.md
        │   │   └── task2.md
        │   └── hooks.py  (optional)

    Args:
        workflow_folders: List of workflow folder names (subdirectories of base_path).
        workflow_names: Optional names to register as. If None, uses folder names.
        base_path: Base path where workflow folders are located.
        host: Server host.
        port: Server port.

    Returns:
        Configured TaskCore instance.
    """
    from tasks.hooks import DynamicWorkflow, WorkflowFactory

    if workflow_names is None:
        workflow_names = workflow_folders

    # Register folder paths with factory
    for folder_name, workflow_name in zip(workflow_folders, workflow_names):
        folder_path = os.path.join(base_path, folder_name)
        WorkflowFactory.register_workflow_folder(workflow_name, folder_path)

    # Create workflows via factory
    workflows = [WorkflowFactory.create(name) for name in workflow_names]

    # Collect all tasks and hooks
    all_tasks = []
    hook_registry: dict[str, callable] = {}

    for workflow in workflows:
        workflow_hooks = workflow.get_hooks()
        workflow_predos = workflow.get_predos()
        for task_def in workflow.get_tasks():
            task_name = task_def["name"]
            # Get hook function from HOOKS dict (keyed by task_name)
            hook_func = workflow_hooks.get(task_name)
            # Get predo function from PREDOS dict (keyed by task_name)
            predo_func = workflow_predos.get(task_name)
            all_tasks.append(Task(
                name=task_name,
                detail=task_def["detail"],
                dependencies=task_def.get("dependencies", []),
                predo=predo_func,
                hook=hook_func,
            ))

    core = TaskCore(tasks=all_tasks, host=host, port=port)

    return core
