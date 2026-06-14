from agent.tools.base import Tool


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found")
        return self.tools[name]

    def get_all_tools(self) -> list[dict]:
        return [tool.get_schema() for tool in self.tools.values()]

    def execute(self, tool_name: str, **kwargs):
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found"
        try:
            return self.tools[tool_name].execute(**kwargs)
        except Exception as e:
            return f"Error: {e}"
