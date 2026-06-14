import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    started_at: str | None = None
    duration: float | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "started_at": self.started_at,
            "duration": self.duration,
            "result": self.result
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            name=data["name"],
            status=TaskStatus(data["status"]),
            started_at=data.get("started_at"),
            duration=data.get("duration"),
            result=data.get("result")
        )


class TaskManager:
    def __init__(self, file_path: str = ".todos.json"):
        self.items: list[Task] = []
        self.file_path = Path(file_path)
        self.load()

    def load(self):
        if not self.file_path.exists():
            return
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            self.items = [Task.from_dict(d) for d in data]
        except (json.JSONDecodeError, KeyError):
            self.items = []

    def add_many(self, names: list[str]) -> list[Task]:
        tasks = []
        for name in names:
            item = Task(name=name)
            self.items.append(item)
            tasks.append(item)
        self.save()
        return tasks

    def start(self, item_id: str) -> Task | None:
        item = self._get(item_id)
        if not item:
            return None
        if item.status != TaskStatus.PENDING:
            return None
        item.status = TaskStatus.IN_PROGRESS
        item.started_at = datetime.now().isoformat()
        self.save()
        return item

    def complete(self, item_id: str, result: str = "") -> Task | None:
        item = self._get(item_id)
        if not item:
            return None
        if item.status != TaskStatus.IN_PROGRESS:
            return None
        item.status = TaskStatus.COMPLETED
        item.result = result
        if item.started_at:
            item.duration = (datetime.now() - datetime.fromisoformat(item.started_at)).total_seconds()
        self.save()
        return item

    def fail(self, item_id: str, error: str = "") -> Task | None:
        item = self._get(item_id)
        if not item:
            return None
        if item.status != TaskStatus.IN_PROGRESS:
            return None
        item.status = TaskStatus.FAILED
        item.result = error
        if item.started_at:
            item.duration = (datetime.now() - datetime.fromisoformat(item.started_at)).total_seconds()
        self.save()
        return item

    def skip(self, item_id: str) -> Task | None:
        item = self._get(item_id)
        if not item:
            return None
        if item.status not in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
            return None
        item.status = TaskStatus.SKIPPED
        self.save()
        return item

    def start_next(self) -> Task | None:
        item = self.get_next()
        if item:
            return self.start(item.id)
        return None

    def get_next(self) -> Task | None:
        for item in self.items:
            if item.status == TaskStatus.PENDING:
                return item
        return None

    def get_progress(self) -> dict:
        total = len(self.items)
        completed = sum(1 for i in self.items if i.status == TaskStatus.COMPLETED)
        failed = sum(1 for i in self.items if i.status == TaskStatus.FAILED)
        in_progress = sum(1 for i in self.items if i.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for i in self.items if i.status == TaskStatus.PENDING)
        skipped = sum(1 for i in self.items if i.status == TaskStatus.SKIPPED)
        return {
            "total": total, "completed": completed, "failed": failed,
            "in_progress": in_progress, "pending": pending, "skipped": skipped
        }

    def save(self):
        data = [item.to_dict() for item in self.items]
        tmp = self.file_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(str(tmp), str(self.file_path))

    def clear(self) -> None:
        self.items = []
        self.save()

    def to_text(self, status_filter: list[TaskStatus] | None = None) -> str:
        icons = {
            TaskStatus.PENDING: "[ ]",
            TaskStatus.IN_PROGRESS: "[~]",
            TaskStatus.COMPLETED: "[x]",
            TaskStatus.FAILED: "[!]",
            TaskStatus.SKIPPED: "[-]",
        }

        lines = []
        for i, item in enumerate(self.items, 1):
            if status_filter and item.status not in status_filter:
                continue
            icon = icons.get(item.status, "[ ]")
            line = f"{icon} {i}. {item.name} (id:{item.id})"
            if item.duration is not None:
                line += f" ({item.duration:.1f}s)"
            if item.result:
                line += f" → {item.result}"
            lines.append(line)
        return "\n".join(lines) if lines else "No tasks"

    def _get(self, item_id: str) -> Task | None:
        for item in self.items:
            if item.id == item_id:
                return item
        return None
