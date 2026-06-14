import os
import subprocess

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

    def __init__(self, workdir: str, timeout: int | None = 60):
        self.workdir = os.path.realpath(workdir)
        self.timeout = timeout

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
