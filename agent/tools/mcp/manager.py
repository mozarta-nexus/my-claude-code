import json
import os
import re
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.client.sse import sse_client

_ENV_PATTERN = re.compile(r"\$\{(\w+)\}")


class MCPToolInfo:
    __slots__ = ("server_name", "tool_name", "description", "input_schema")

    def __init__(
        self, server_name: str, tool_name: str, description: str, input_schema: dict
    ):
        self.server_name = server_name
        self.tool_name = tool_name
        self.description = description
        self.input_schema = input_schema


class MCPClientManager:
    def __init__(self, config_path: str = "mcp.json"):
        self._sessions: dict[str, ClientSession] = {}
        self._exit_stacks: dict[str, AsyncExitStack] = {}
        self._tool_map: dict[str, MCPToolInfo] = {}
        self._config_path = Path(config_path)

    async def connect_all(self) -> None:
        config = self._load_config()
        for name, server_config in config.items():
            try:
                await self.connect_server(name, server_config)
            except Exception as e:
                print(f"[MCP] Failed to connect '{name}': {e}")

    async def connect_server(self, server_name: str, server_config: dict) -> None:
        if "command" in server_config:
            await self._connect_stdio(server_name, server_config)
        elif "url" in server_config:
            await self._connect_sse(server_name, server_config)
        else:
            raise ValueError(f"Server '{server_name}': must have 'command' or 'url'")

    async def _connect_stdio(self, name: str, config: dict):
        env = self._resolve_env(config.get("env", {}))
        params = StdioServerParameters(
            command=config["command"], args=config.get("args", []), env=env or None
        )

        stack = AsyncExitStack()
        read_stream, write_stream = await stack.enter_async_context(
            stdio_client(params)
        )
        session = await stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        self._exit_stacks[name] = stack
        self._sessions[name] = session
        await self._discover_tools(name, session)
        print(f"[MCP] Connected '{name}' (stdio)")

    async def _connect_sse(self, name: str, config: dict):
        stack = AsyncExitStack()
        read_stream, write_stream = await stack.enter_async_context(
            sse_client(config["url"])
        )
        session = await stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        self._exit_stacks[name] = stack
        self._sessions[name] = session
        await self._discover_tools(name, session)
        print(f"[MCP] Connected '{name}' (sse)")

    async def _discover_tools(self, name: str, session: ClientSession):
        results = await session.list_tools()
        for tool in results.tools:
            info = MCPToolInfo(
                server_name=name,
                tool_name=tool.name,
                description=tool.description or "",
                input_schema=tool.inputSchema or {"type": "object", "properties": {}},
            )
            self._tool_map[tool.name] = info

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        info = self._tool_map.get(tool_name)
        if not info:
            return f"Error: MCP tool '{tool_name}' not found"
        session = self._sessions.get(info.server_name)
        if not session:
            return f"Error: MCP server '{info.server_name}' not connected"

        try:
            print(
                f"[MCP] Calling tool '{tool_name}' on server '{info.server_name}' with arguments: {arguments}"
            )
            res = await session.call_tool(tool_name, arguments)
            result = self._format_result(res)
            print(
                f"[MCP] Tool '{tool_name}' returned: {result[:200]}{'...' if len(result) > 200 else ''}"
            )
            return result
        except Exception as e:
            print(f"[MCP] Tool '{tool_name}' call failed: {e}")
            return f"Error: MCP call failed: {e}"

    def get_all_tool_schemas(self) -> list[dict]:
        schemas = []
        for tool_name, info in self._tool_map.items():
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": info.description,
                        "parameters": info.input_schema,
                    },
                }
            )
        return schemas

    def get_tool_infos(self) -> list[MCPToolInfo]:
        return list(self._tool_map.values())

    async def shutdown(self):
        for name, stack in self._exit_stacks.items():
            try:
                await stack.aclose()
            except Exception as e:
                print(f"[MCP] Error closing '{name}': {e}")
        self._exit_stacks.clear()
        self._sessions.clear()
        self._tool_map.clear()

    def _load_config(self) -> dict:
        if not self._config_path.exists():
            return {}
        data = json.loads(self._config_path.read_text(encoding="utf-8"))
        return data.get("mcpServers", {})

    @staticmethod
    def _resolve_env(env: dict) -> dict:
        resolved = {}
        for key, value in env.items():
            if isinstance(value, str):
                resolved[key] = _ENV_PATTERN.sub(
                    lambda m: os.environ.get(m.group(1), ""), value
                )
            else:
                resolved[key] = str(value)
        return resolved

    @staticmethod
    def _format_result(result) -> str:
        if hasattr(result, "content") and result.content:
            texts = []
            for item in result.content:
                if hasattr(item, "text"):
                    texts.append(item.text)
                elif hasattr(item, "data"):
                    texts.append(item.data)
            return "\n".join(texts) if texts else str(result)
        return str(result)
