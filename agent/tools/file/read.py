import os

from agent.tools.file.base import FileTool


MAX_CONTENT_LEN = 5000


class ReadFile(FileTool):
    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "读取指定路径文件的内容，支持按行偏移和限制，内容过大时截断返回前5000字符"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要读取的文件路径"},
                "offset": {"type": "integer", "description": "从第几行开始读取，默认1"},
                "limit": {
                    "type": "integer",
                    "description": "最多读取的行数，默认读取全部",
                },
            },
            "required": ["path"],
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        if not path:
            raise ValueError("path is required")
        offset = kwargs.get("offset", 1)
        limit = kwargs.get("limit")
        self._print_call(**kwargs)
        real_path = self.validate_path(path)
        if not os.path.isfile(real_path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(real_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        selected = lines[offset - 1 :]
        if limit is not None:
            selected = selected[:limit]
        result = "".join(selected)
        if len(result) > MAX_CONTENT_LEN:
            result = result[:MAX_CONTENT_LEN] + "\n... (truncated)"
        self._print_result(result)
        return result
