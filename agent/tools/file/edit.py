import os

from agent.tools.base import TAG, RESET
from agent.tools.file.base import FileTool


class EditFile(FileTool):
    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "对指定文件进行精确字符串替换，将old_string替换为new_string"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要编辑的文件路径"},
                "old_string": {"type": "string", "description": "要被替换的原字符串"},
                "new_string": {"type": "string", "description": "替换后的新字符串"},
            },
            "required": ["path", "old_string", "new_string"],
        }

    def _print_call(self, **kwargs):
        print(f"  {TAG}[{self.name}]{RESET} {kwargs.get('path', '')}")

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        old_string = kwargs.get("old_string")
        new_string = kwargs.get("new_string")
        if not path:
            raise ValueError("path is required")
        if old_string is None:
            raise ValueError("old_string is required")
        if new_string is None:
            raise ValueError("new_string is required")
        self._print_call(**kwargs)
        real_path = self.validate_path(path)
        if not os.path.isfile(real_path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(real_path, "r", encoding="utf-8") as f:
            content = f.read()
        count = content.count(old_string)
        if count == 0:
            raise ValueError(f"old_string not found in {path}")
        if count > 1:
            raise ValueError(
                f"old_string found {count} times in {path}, must be unique"
            )
        content = content.replace(old_string, new_string)
        with open(real_path, "w", encoding="utf-8") as f:
            f.write(content)
        result = f"Successfully edited {path}"
        self._print_result(result)
        return result
