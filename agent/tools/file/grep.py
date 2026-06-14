import os
import re

from agent.tools.base import TAG, RESET
from agent.tools.file.base import FileTool


class GrepFile(FileTool):
    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return "在指定目录下搜索匹配正则表达式的文件内容，返回匹配的文件路径和行号"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "要搜索的正则表达式"},
                "path": {
                    "type": "string",
                    "description": "要搜索的目录或文件路径，默认为根目录",
                },
                "include": {
                    "type": "string",
                    "description": "文件名过滤模式，如 *.py，默认搜索所有文件",
                },
            },
            "required": ["pattern"],
        }

    def _print_call(self, **kwargs):
        print(f"  {TAG}[{self.name}]{RESET} {kwargs.get('pattern', '')}")

    def execute(self, **kwargs) -> str:
        pattern = kwargs.get("pattern")
        path = kwargs.get("path", ".")
        include = kwargs.get("include")
        if not pattern:
            raise ValueError("pattern is required")
        self._print_call(**kwargs)
        real_path = self.validate_path(path)
        regex = re.compile(pattern)
        matches = []
        if os.path.isfile(real_path):
            matches = self._search_file(real_path, regex)
        elif os.path.isdir(real_path):
            matches = self._search_dir(real_path, regex, include)
        else:
            raise FileNotFoundError(f"Path not found: {path}")
        if not matches:
            result = "No matches found"
        else:
            result = "\n".join(matches)
        self._print_result(result)
        return result

    def _search_file(self, file_path: str, regex: re.Pattern) -> list[str]:
        results = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if regex.search(line):
                        results.append(f"{file_path}:{line_num}: {line.rstrip()}")
        except (OSError, UnicodeDecodeError):
            pass
        return results

    def _search_dir(
        self, dir_path: str, regex: re.Pattern, include: str | None
    ) -> list[str]:
        results = []
        for root, _, files in os.walk(dir_path):
            for filename in files:
                if include and not self._match_include(filename, include):
                    continue
                file_path = os.path.join(root, filename)
                results.extend(self._search_file(file_path, regex))
        return results

    @staticmethod
    def _match_include(filename: str, include: str) -> bool:
        import fnmatch

        return fnmatch.fnmatch(filename, include)
