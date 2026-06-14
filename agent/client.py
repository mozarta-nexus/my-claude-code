import asyncio
import os

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner

from agent.core import Agent
from agent.events import ThinkingEvent, StreamEvent, ToolCallEvent, ToolResultEvent
from agent.llm.base import LLMClient
from agent.tools.bash.terminal import TerminalTool
from agent.tools.file.edit import EditFile
from agent.tools.file.glob import GlobFile
from agent.tools.file.grep import GrepFile
from agent.tools.file.read import ReadFile
from agent.tools.file.write import WriteFile
from agent.tools.mcp.adapter import MCPToolAdapter
from agent.tools.mcp.manager import MCPClientManager
from agent.tools.planning.add_tasks import AddTasks
from agent.tools.planning.list_tasks import ListTasks
from agent.tools.planning.planner import TaskManager
from agent.tools.planning.update_task import UpdateTask
from agent.tools.registry import ToolRegistry
from agent.tools.skills.load_skill import LoadSkill
from agent.tools.skills.skills import SkillsManager
from agent.tools.web.fetch import WebFetch

console = Console()


class Renderer:
    def __init__(self):
        self._live: Live | None = None
        self._content_buffer = ""

    def on_thinking(self, event: ThinkingEvent):
        self._flush_live()
        self._live = Live(Spinner("dots", text="思考中..."), console=console, vertical_overflow="visible")
        self._live.start()

    def on_stream(self, event: StreamEvent):
        self._content_buffer += event.token
        if self._live is None:
            self._live = Live(Markdown(self._content_buffer), console=console, vertical_overflow="visible")
            self._live.start()
        else:
            self._live.update(Markdown(self._content_buffer))

    def on_tool_call(self, event: ToolCallEvent):
        self._flush_live()
        args_lines = []
        for k, v in event.arguments.items():
            args_lines.append(f" {k} = {v!r}")
        args_text = "\n".join(args_lines) if args_lines else " (无参数)"
        console.print(Panel(
            args_text,
            title=f"🔧 {event.name}",
            border_style="blue",
            padding=(0, 2),
        ))

    def on_tool_result(self, event: ToolResultEvent):
        self._flush_live()
        display = event.result[:500]
        if len(event.result) > 500:
            display += "\n..."
        console.print(Panel(
            display,
            title=f"✅ {event.name} ({event.duration:.2f}s)",
            border_style="green",
            padding=(0, 2),
        ))

    def _flush_live(self):
        if self._live:
            self._live.stop()
            self._live = None
            self._content_buffer = ""

    def flush(self):
        self._flush_live()


WORK_DIR = os.getcwd()
SYSTEM_PROMPT = f"""你叫小帅，是一个AI编程助手，工作在{WORK_DIR}

你必须遵守以下规则：
1. 对于需要多个步骤才能完成的任务，你必须先使用 add_tasks 批量添加所有步骤，然后按顺序执行
2. 每开始一个步骤前，使用 update_task(action="start", task_id=...) 标记为进行中；完成后使用 update_task(action="complete", task_id=...) 标记完成；失败则使用 update_task(action="fail", task_id=...)
3. 也可以使用 update_task(action="start_next") 自动开始下一个待执行任务
4. 随时可以使用 list_tasks 查看当前任务进度，支持按状态过滤
5. 一次只执行一个任务步骤，不要并行处理
6. 对于单步骤的简单问题，无需创建任务，直接回答即可"""

EXIT_COMMANDS = {"exit", "quit", "q"}


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(ReadFile(root_dir=WORK_DIR))
    registry.register(WriteFile(root_dir=WORK_DIR))
    registry.register(EditFile(root_dir=WORK_DIR))
    registry.register(GlobFile(root_dir=WORK_DIR))
    registry.register(GrepFile(root_dir=WORK_DIR))
    registry.register(WebFetch())
    registry.register(TerminalTool(workdir=WORK_DIR))

    task_manager = TaskManager()
    registry.register(AddTasks(task_manager))
    registry.register(UpdateTask(task_manager))
    registry.register(ListTasks(task_manager))

    return registry


async def setup_mcp(registry: ToolRegistry) -> MCPClientManager | None:
    manager = MCPClientManager(config_path=".mcps/mcp.json")
    await manager.connect_all()
    if not manager.get_tool_infos():
        print("[MCP] No servers configured or all connections failed")
        await manager.shutdown()
        return None
    for info in manager.get_tool_infos():
        registry.register(MCPToolAdapter(mcp_manager=manager, mcp_tool=info))
    print(f"[MCP] {len(manager.get_tool_infos())} tools registered")
    return manager


def setup_skills(registry: ToolRegistry) -> SkillsManager:
    manager = SkillsManager(skills_dir=".skills")
    if manager.skills:
        registry.register(LoadSkill(manager=manager))
    return manager


def build_system_prompt(skills_manager: SkillsManager) -> str:
    prompt = SYSTEM_PROMPT
    summaries = skills_manager.format_summaries()
    if summaries:
        prompt += f"\n\n{summaries}"
    return prompt


async def chat():
    registry = create_tool_registry()
    mcp_manager = await setup_mcp(registry)
    skills_manager = setup_skills(registry)

    renderer = Renderer()

    agent = Agent(
        client=LLMClient(),
        system_prompt=build_system_prompt(skills_manager),
        tool_registry=registry,
    )

    try:
        while True:
            user_input = input("User> ")
            if not user_input:
                continue
            if user_input.strip().lower() in EXIT_COMMANDS:
                console.print("[dim]Bye![/dim]")
                break
            for event in agent.run(user_input):
                if isinstance(event,ThinkingEvent):
                    renderer.on_thinking(event)
                elif isinstance(event,StreamEvent):
                    renderer.on_stream(event)
                elif isinstance(event,ToolCallEvent):
                    renderer.on_tool_call(event)
                elif isinstance(event,ToolResultEvent):
                    renderer.on_tool_result(event)
                renderer.flush()
    finally:
        if mcp_manager:
            await mcp_manager.shutdown()


if __name__ == "__main__":
    asyncio.run(chat())
