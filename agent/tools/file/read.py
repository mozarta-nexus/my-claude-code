import os

from agent.tools.file.base import FileTool


class ReadFile(FileTool):
    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "读取指定路径文件的全部内容"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要读取的文件路径"}
            },
            "required": ["path"],
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        if not path:
            raise ValueError("path is required")
        self._print_call(**kwargs)
        real_path = self.validate_path(path)
        if not os.path.isfile(real_path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(real_path, "r", encoding="utf-8") as f:
            result = f.read()
        self._print_result(result)
        return result
