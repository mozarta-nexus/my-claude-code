from agent.tools.base import Tool, TAG, RESET
from agent.tools.planning.planner import TaskManager


class UpdateTask(Tool):
    def __init__(self, manager: TaskManager):
        self.manager = manager

    @property
    def name(self) -> str:
        return "update_task"

    @property
    def description(self) -> str:
        return (
            "更新任务状态。"
            "start: 开始执行任务（PENDING→IN_PROGRESS）；"
            "complete: 标记任务完成（IN_PROGRESS→COMPLETED）；"
            "fail: 标记任务失败（IN_PROGRESS→FAILED）；"
            "skip: 跳过任务（PENDING/IN_PROGRESS→SKIPPED）；"
            "start_next: 自动开始下一个待执行任务（无需指定task_id）。"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "complete", "fail", "skip", "start_next"],
                    "description": "状态变更操作",
                },
                "task_id": {
                    "type": "string",
                    "description": "任务ID（start_next 操作时无需提供）",
                },
                "result": {
                    "type": "string",
                    "description": "complete 时的执行结果，或 fail 时的失败原因",
                },
            },
            "required": ["action"],
        }

    def execute(self, **kwargs) -> str:
        action = kwargs.get("action")
        task_id = kwargs.get("task_id", "")
        result_text = kwargs.get("result", "")
        self._print_call(**kwargs)

        if action == "start":
            task = self.manager.start(task_id)
            if not task:
                return f"Error: task '{task_id}' not found or not in PENDING status"
            return f"Started: [{task.id}] {task.name}"

        elif action == "complete":
            task = self.manager.complete(task_id, result_text)
            if not task:
                return f"Error: task '{task_id}' not found or not in IN_PROGRESS status"
            msg = f"Completed: [{task.id}] {task.name}"
            if task.duration is not None:
                msg += f" ({task.duration:.1f}s)"
            return msg

        elif action == "fail":
            task = self.manager.fail(task_id, result_text)
            if not task:
                return f"Error: task '{task_id}' not found or not in IN_PROGRESS status"
            return f"Failed: [{task.id}] {task.name} — {result_text}"

        elif action == "skip":
            task = self.manager.skip(task_id)
            if not task:
                return f"Error: task '{task_id}' not found or not skippable"
            return f"Skipped: [{task.id}] {task.name}"

        elif action == "start_next":
            task = self.manager.start_next()
            if not task:
                return "No pending tasks to start"
            return f"Started next: [{task.id}] {task.name}"

        else:
            return f"Error: unknown action '{action}'"