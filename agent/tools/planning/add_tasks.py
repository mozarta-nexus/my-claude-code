from agent.tools.base import Tool, TAG, RESET
from agent.tools.planning.planner import TaskManager, TaskStatus


class AddTasks(Tool):
    def __init__(self, manager: TaskManager):
        self.manager = manager

    @property
    def name(self) -> str:
        return "add_tasks"

    @property
    def description(self) -> str:
        return "批量添加任务到任务列表。规划时一次性添加所有步骤，避免多次调用。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "任务名称列表，按执行顺序排列",
                },
            },
            "required": ["tasks"],
        }

    def execute(self, **kwargs) -> str:
        tasks = kwargs.get("tasks", [])
        if not tasks:
            return "Error: tasks is required and must be non-empty"
        self._print_call(**kwargs)
        added = self.manager.add_many(tasks)
        lines = [f"[{t.id}] {t.name}" for t in added]
        result = f"Added {len(added)} tasks:\n" + "\n".join(lines)
        self._print_result(result)
        return result