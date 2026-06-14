from agent.tools.base import Tool, TAG, RESET
from agent.tools.planning.planner import TaskManager, TaskStatus


class ListTasks(Tool):
    def __init__(self, manager: TaskManager):
        self.manager = manager

    @property
    def name(self) -> str:
        return "list_tasks"

    @property
    def description(self) -> str:
        return "查看任务列表和进度。可按状态过滤，不传 filter 则显示全部。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "failed", "skipped"],
                    "description": "按状态过滤任务，不传则显示全部",
                },
            },
            "required": [],
        }

    def execute(self, **kwargs) -> str:
        self._print_call(**kwargs)
        status_filter = kwargs.get("filter")
        progress = self.manager.get_progress()

        filter_statuses = None
        if status_filter:
            filter_statuses = [TaskStatus(status_filter)]

        task_text = self.manager.to_text(filter_statuses)
        header = (
            f"Progress: {progress['completed']}/{progress['total']} done | "
            f"{progress['in_progress']} active | {progress['failed']} failed | "
            f"{progress['pending']} pending | {progress['skipped']} skipped"
        )
        result = f"{header}\n{task_text}"
        self._print_result(result)
        return result
