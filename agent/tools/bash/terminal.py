import os
import re
import subprocess
from enum import Enum
from pathlib import Path

from agent.tools.base import Tool


class TerminalTool(Tool):
    AUTO_APPROVE_PATTERNS = [
        r"^git status",
        r"^git log",
        r"^git diff",
        r"^git branch",
        r"^ls\b",
        r"^cat\b",
        r"^head\b",
        r"^tail\b",
        r"^find\b",
        r"^grep\b",
        r"^wc\b",
        r"^python.*-m\s+pytest",
        r"^python.*-m\s+unittest",
        r"^go test",
        r"^cargo test",
        r"^npm test",
    ]

    BLOCKED_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+~",
        r"format\s+[A-Z]:",
        r"curl.*\|\s*(ba)?sh",
        r"wget.*\|\s*(ba)?sh",
        r"dd\s+if=",
        r":\(\)\{\s*:\|:&\s*\}",
        r"mkfs",
        r"shutdown",
        r"reboot",
    ]

    def __init__(self, workdir: str = ".", timeout: int | None = 60, max_output: int = 5000,
                 confirm_require: bool = True):
        self.workdir = Path(workdir).resolve()
        self.timeout = timeout
        self.max_output = max_output
        self.confirm_require = confirm_require

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def description(self) -> str:
        return "执行shell命令，在项目根目录下执行"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的shell命令"
                },
                "timeout": {
                    "type": "number",
                    "description": f"命令执行的超时时间，默认值为 {self.timeout}",
                    "default": self.timeout
                },
            },
            "required": ["command"]
        }

    def execute(self, **kwargs) -> str:
        command = kwargs.get("command")
        timeout = kwargs.get("timeout", self.timeout)
        self._print_call(**kwargs)

        safety = self._validate(command)
        if safety == CommandSafety.BLOCKED:
            return f"命令被禁止执行： {command}\n 该命令可能造出不可逆的损害"
        if safety == CommandSafety.NEEDS_CONFIRM and self.confirm_require:
            confirm = input(f"\n⚠️  确认执行命令: {command}\n输入 'y' 确认: ").strip().lower()
            if confirm != 'y':
                return "用户拒绝执行该命令"
        return self._execute(command, timeout)

    def _execute(self, command: str | None, timeout: int | None) -> str:
        try:
            res = subprocess.run(
                command, shell=True, timeout=timeout,
                capture_output=True, text=True, cwd=self.workdir,
            )
        except subprocess.TimeoutExpired:
            result = f"Error: Command timed out after {timeout}s"
            self._print_result(result)
            return result
        except Exception as e:
            result = f"Error: {e}"
            self._print_result(result)
            return result

        output = res.stdout + res.stderr
        if res.returncode == 0:
            result = f"exit_code: {res.returncode}, output: {output}"
        else:
            result = f"exit_code: {res.returncode}, output: {output}"
        self._print_result(result)
        return result

    def _validate(self, command):
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, command):
                return CommandSafety.BLOCKED

        for pattern in self.AUTO_APPROVE_PATTERNS:
            if re.search(pattern, command):
                return CommandSafety.AUTO_APPROVE

        return CommandSafety.NEEDS_CONFIRM


class CommandSafety(Enum):
    BLOCKED = "blocked",
    NEEDS_CONFIRM = "needs_confirm",
    AUTO_APPROVE = "auto_approve"
