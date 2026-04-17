"""
Workflow templates and hook factory.

DynamicWorkflow reads a workflow folder and creates a class automatically.
"""
import importlib.util
import os


class WorkflowTemplate:
    """Base class for workflow templates."""

    def __init__(self, core=None):
        self.core = core

    def get_tasks(self) -> list[dict]:
        """Return list of task definitions."""
        raise NotImplementedError

    def get_hooks(self) -> dict[str, callable]:
        """Return dict mapping task names to hook functions."""
        return {}

    def get_predos(self) -> dict[str, callable]:
        """Return dict mapping task names to predo functions."""
        return {}


def _parse_task_md(md_content: str) -> dict:
    """Parse a task md file into a dict."""
    lines = md_content.strip().split("\n")
    result = {
        "name": "",
        "detail": "",
        "dependencies": [],
        "predo": None,
        "hook": None,
    }

    current_field = None
    field_content = []

    for line in lines:
        line_stripped = line.strip()

        if line_stripped.startswith("#"):
            result["name"] = line_stripped.lstrip("#").strip()
            continue

        if not line_stripped:
            continue

        if line_stripped.startswith("detail:"):
            if current_field == "detail":
                result["detail"] = "\n".join(field_content).strip()
            elif current_field == "dependencies" and field_content:
                deps = field_content[0].strip()
                if deps:
                    result["dependencies"] = [d.strip() for d in deps.split(",")]
            elif current_field == "predo" and field_content:
                predo_name = field_content[0].strip()
                if predo_name:
                    result["predo"] = predo_name
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
            elif current_field == "predo" and field_content:
                predo_name = field_content[0].strip()
                if predo_name:
                    result["predo"] = predo_name
            elif current_field == "hook" and field_content:
                hook_name = field_content[0].strip()
                if hook_name:
                    result["hook"] = hook_name
            current_field = "dependencies"
            content = line_stripped[len("dependencies:"):].strip()
            field_content = [content] if content else []
        elif line_stripped.startswith("predo:"):
            if current_field == "detail":
                result["detail"] = "\n".join(field_content).strip()
            elif current_field == "dependencies" and field_content:
                deps = field_content[0].strip()
                if deps:
                    result["dependencies"] = [d.strip() for d in deps.split(",")]
            elif current_field == "predo" and field_content:
                predo_name = field_content[0].strip()
                if predo_name:
                    result["predo"] = predo_name
            elif current_field == "hook" and field_content:
                hook_name = field_content[0].strip()
                if hook_name:
                    result["hook"] = hook_name
            current_field = "predo"
            content = line_stripped[len("predo:"):].strip()
            field_content = [content] if content else []
        elif line_stripped.startswith("hook:"):
            if current_field == "detail":
                result["detail"] = "\n".join(field_content).strip()
            elif current_field == "dependencies" and field_content:
                deps = field_content[0].strip()
                if deps:
                    result["dependencies"] = [d.strip() for d in deps.split(",")]
            elif current_field == "predo" and field_content:
                predo_name = field_content[0].strip()
                if predo_name:
                    result["predo"] = predo_name
            elif current_field == "hook" and field_content:
                hook_name = field_content[0].strip()
                if hook_name:
                    result["hook"] = hook_name
            current_field = "hook"
            content = line_stripped[len("hook:"):].strip()
            field_content = [content] if content else []
        else:
            field_content.append(line_stripped)

    if current_field == "detail":
        result["detail"] = "\n".join(field_content).strip()
    elif current_field == "dependencies" and field_content:
        deps = field_content[0].strip()
        if deps:
            result["dependencies"] = [d.strip() for d in deps.split(",")]
    elif current_field == "predo" and field_content:
        predo_name = field_content[0].strip()
        if predo_name:
            result["predo"] = predo_name
    elif current_field == "hook" and field_content:
        hook_name = field_content[0].strip()
        if hook_name:
            result["hook"] = hook_name

    return result


class DynamicWorkflow(WorkflowTemplate):
    """
    Workflow that dynamically reads task definitions and hooks from a folder.

    Folder structure:
        workflow_folder/
        ├── tasks/
        │   ├── task1.md
        │   └── task2.md
        ├── hooks.py   (optional)
        └── workflow.py  (required, defines WORKFLOW chain)
    """

    _cache: dict[str, "DynamicWorkflow"] = {}

    def __init__(self, folder_path: str, core=None):
        """
        Initialize DynamicWorkflow from a folder path.

        Args:
            folder_path: Path to the workflow folder.
            core: Optional core reference.
        """
        super().__init__(core)
        self.folder_path = folder_path
        self._tasks: list[dict] = []
        self._hooks: dict[str, callable] = {}
        self._predos: dict[str, callable] = {}
        self._workflow_chain: str = ""
        self._load()

    def _load(self) -> None:
        """Load tasks, hooks, and workflow chain from folder."""
        tasks_dir = os.path.join(self.folder_path, "tasks")
        hooks_path = os.path.join(self.folder_path, "hooks.py")
        workflow_path = os.path.join(self.folder_path, "workflow.py")

        # Load workflow chain
        if os.path.isfile(workflow_path):
            workflow_module = self._import_module(workflow_path, "workflow")
            if hasattr(workflow_module, "WORKFLOW"):
                self._workflow_chain = workflow_module.WORKFLOW

        # Load tasks from md files
        if os.path.isdir(tasks_dir):
            tasks_by_name = {}
            for filename in sorted(os.listdir(tasks_dir)):
                if not filename.endswith(".md"):
                    continue
                md_path = os.path.join(tasks_dir, filename)
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                task_def = _parse_task_md(md_content)
                if task_def["name"]:
                    tasks_by_name[task_def["name"]] = task_def

            # Apply workflow chain dependencies
            self._apply_workflow_deps(tasks_by_name)

            self._tasks = list(tasks_by_name.values())

        # Load hooks from hooks.py
        if os.path.isfile(hooks_path):
            hooks_module = self._import_module(hooks_path, "hooks")
            if hasattr(hooks_module, "HOOKS"):
                self._hooks = hooks_module.HOOKS
            if hasattr(hooks_module, "PREDOS"):
                self._predos = hooks_module.PREDOS

    def _apply_workflow_deps(self, tasks_by_name: dict) -> None:
        """Apply dependencies from workflow chain to tasks."""
        if not self._workflow_chain:
            return

        # Parse workflow chains (split by ';')
        for chain in self._workflow_chain.split(";"):
            chain = chain.strip()
            if not chain:
                continue

            # Check for multi-dependency syntax: "task:dep1,dep2,dep3"
            if ":" in chain:
                task_name, deps_str = chain.split(":", 1)
                task_name = task_name.strip()
                deps = [d.strip() for d in deps_str.split(",") if d.strip()]
                if task_name in tasks_by_name:
                    task_def = tasks_by_name[task_name]
                    existing_deps = set(task_def.get("dependencies", []))
                    existing_deps.update(deps)
                    task_def["dependencies"] = list(existing_deps)
                continue

            # Linear chain: "task1,task2,task3"
            task_names = [t.strip() for t in chain.split(",")]
            for i, task_name in enumerate(task_names):
                if task_name not in tasks_by_name:
                    continue
                if i > 0:
                    prev_task = task_names[i - 1]
                    task_def = tasks_by_name[task_name]
                    deps = set(task_def.get("dependencies", []))
                    deps.add(prev_task)
                    task_def["dependencies"] = list(deps)

    def _import_module(self, module_path: str, base_name: str):
        """Import a Python module from file path."""
        module_name = f"workflow_{base_name}_{os.path.basename(os.path.dirname(module_path))}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def get_tasks(self) -> list[dict]:
        return self._tasks

    def get_hooks(self) -> dict[str, callable]:
        return self._hooks

    def get_predos(self) -> dict[str, callable]:
        return self._predos


class WorkflowFactory:
    """Factory for creating workflow instances."""

    _workflows: dict[str, type[WorkflowTemplate]] = {}
    _workflow_folders: dict[str, str] = {}

    @classmethod
    def register_workflow(cls, name: str, workflow_class: type[WorkflowTemplate]) -> None:
        """Register a workflow class."""
        cls._workflows[name] = workflow_class

    @classmethod
    def register_workflow_folder(cls, name: str, folder_path: str) -> None:
        """Register a workflow folder path for dynamic loading."""
        cls._workflow_folders[name] = folder_path

    @classmethod
    def create(cls, name: str) -> WorkflowTemplate:
        """
        Create a workflow instance by name.

        If a folder path is registered, creates a DynamicWorkflow.
        Otherwise uses a registered class.
        """
        if name in cls._workflow_folders:
            return DynamicWorkflow(cls._workflow_folders[name])

        if name in cls._workflows:
            return cls._workflows[name]()

        raise ValueError(
            f"Unknown workflow: {name}. "
            f"Available: {list(cls._workflow_folders.keys()) + list(cls._workflows.keys())}"
        )

    @classmethod
    def create_all(cls) -> list[WorkflowTemplate]:
        """Create all registered workflows."""
        all_workflows = []
        for name in cls._workflow_folders:
            all_workflows.append(cls.create(name))
        for name in cls._workflows:
            all_workflows.append(cls.create(name))
        return all_workflows
