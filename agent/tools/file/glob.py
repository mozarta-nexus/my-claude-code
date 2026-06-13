import glob as glob_module

from agent.tools.file.base import FileTool


class GlobFile(FileTool):
    @property
    def name(self) -> str:
        return "glob"

    @property
    def description(self) -> str:
        return "根据通配符模式搜索匹配的文件路径"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "glob通配符模式，如 **/*.py、src/**/*.ts",
                },
            },
            "required": ["pattern"],
        }

    def execute(self, **kwargs) -> str:
        pattern = kwargs.get("pattern")
        if not pattern:
            raise ValueError("pattern is required")
        self._print_call(**kwargs)
        matches = glob_module.glob(pattern, recursive=True)
        if not matches:
            result = "No files matched the pattern"
        else:
            result = "\n".join(matches)
        self._print_result(result)
        return result
