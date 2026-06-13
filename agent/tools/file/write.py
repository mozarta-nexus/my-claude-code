import os

from agent.tools.base import TAG, RESET
from agent.tools.file.base import FileTool


class WriteFile(FileTool):
    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "将内容写入指定路径的文件，若文件已存在则覆盖"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要写入的文件路径"},
                "content": {"type": "string", "description": "要写入的文件内容"},
            },
            "required": ["path", "content"],
        }

    def _print_call(self, **kwargs):
        print(f"  {TAG}[{self.name}]{RESET} {kwargs.get('path', '')}")

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        content = kwargs.get("content")
        if not path:
            raise ValueError("path is required")
        if content is None:
            raise ValueError("content is required")
        self._print_call(**kwargs)
        real_path = self.validate_path(path)
        dir_path = os.path.dirname(real_path)
        if dir_path and not os.path.isdir(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        with open(real_path, "w", encoding="utf-8") as f:
            f.write(content)
        result = f"Successfully wrote to {path}"
        self._print_result(result)
        return result
