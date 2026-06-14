import asyncio
import os

from agent.Agent import Agent
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
from agent.tools.web.fetch import WebFetch

WORK_DIR = os.getcwd()
SYSTEM = f"""你叫小帅，是一个AI编程助手，工作在{WORK_DIR}

你必须遵守以下规则：
1. 对于需要多个步骤才能完成的任务，你必须先使用 add_tasks 批量添加所有步骤，然后按顺序执行
2. 每开始一个步骤前，使用 update_task(action="start", task_id=...) 标记为进行中；完成后使用 update_task(action="complete", task_id=...) 标记完成；失败则使用 update_task(action="fail", task_id=...)
3. 也可以使用 update_task(action="start_next") 自动开始下一个待执行任务
4. 随时可以使用 list_tasks 查看当前任务进度，支持按状态过滤
5. 一次只执行一个任务步骤，不要并行处理
6. 对于单步骤的简单问题，无需创建任务，直接回答即可"""


async def setup_mcp(tool_registry: ToolRegistry) -> MCPClientManager | None:
    manager = MCPClientManager(config_path="mcps/mcp.json")
    await manager.connect_all()
    if not manager.get_tool_infos():
        print("[MCP] No MCP servers configured or all connections failed")
        await manager.shutdown()
        return None
    for tool_info in manager.get_tool_infos():
        adapter = MCPToolAdapter(mcp_manager=manager, mcp_tool=tool_info)
        tool_registry.register(adapter)
    print(f"[MCP] {len(manager.get_tool_infos())} tools registered")
    return manager


async def run(tool_registry: ToolRegistry):
    mcp_manager = await setup_mcp(tool_registry)

    client = LLMClient()
    agent = Agent(client=client, system_prompt=SYSTEM, tool_registry=tool_registry)

    try:
        while True:
            user_input = input("User> ")
            if not user_input:
                continue
            if user_input.strip().lower() in ("exit", "quit", "q"):
                print("Bye!")
                break
            res = agent.run(user_input)
            print(f"AI> {res}")
    finally:
        if mcp_manager:
            await mcp_manager.shutdown()


if __name__ == "__main__":
    tool_registry = ToolRegistry()
    tool_registry.register(ReadFile(root_dir=WORK_DIR))
    tool_registry.register(WriteFile(root_dir=WORK_DIR))
    tool_registry.register(EditFile(root_dir=WORK_DIR))
    tool_registry.register(GlobFile(root_dir=WORK_DIR))
    tool_registry.register(GrepFile(root_dir=WORK_DIR))
    tool_registry.register(WebFetch())
    tool_registry.register(TerminalTool(workdir=WORK_DIR))

    task_manager = TaskManager()
    tool_registry.register(AddTasks(task_manager))
    tool_registry.register(UpdateTask(task_manager))
    tool_registry.register(ListTasks(task_manager))

    asyncio.run(run(tool_registry))
