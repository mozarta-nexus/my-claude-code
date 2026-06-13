import os

from agent.tools.base import Tool


class FileTool(Tool):
    def __init__(self, root_dir: str):
        self.root_dir = os.path.realpath(root_dir)

    def validate_path(self, path: str) -> str:
        real_path = os.path.realpath(path)
        if not real_path.startswith(self.root_dir):
            raise PermissionError(f"Path '{path}' is outside the root directory")
        return real_path
