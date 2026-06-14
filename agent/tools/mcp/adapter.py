import asyncio
import concurrent.futures

from agent.tools.base import Tool
from agent.tools.mcp.manager import MCPClientManager, MCPToolInfo


class MCPToolAdapter(Tool):

    def __init__(self, mcp_manager: MCPClientManager, mcp_tool: MCPToolInfo):
        self.manager = mcp_manager
        self.mcp_tool = mcp_tool

    @property
    def name(self) -> str:
        return self.mcp_tool.tool_name

    @property
    def description(self) -> str:
        return self.mcp_tool.description

    @property
    def parameters(self) -> dict:
        return self.mcp_tool.input_schema

    def execute(self, **kwargs) -> str:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self.manager.call_tool(self.mcp_tool.tool_name, kwargs)
                )
                return future.result(timeout=120)
        else:
            return asyncio.run(
                self.manager.call_tool(self.mcp_tool.tool_name, kwargs)
            )
