import json

from agent.data import Message
from agent.llm.base import LLMClient
from agent.tools.registry import ToolRegistry


class Agent:
    def __init__(
        self, client: LLMClient, system_prompt: str, tool_registry: ToolRegistry
    ):
        self.client = client
        self.system_prompt = system_prompt
        self.tool_registry = tool_registry
        self.history = []

    def run(self, user_input: str):
        self.history.append(Message(role="user", content=user_input))
        while True:
            messages = []
            if self.system_prompt:
                messages.append(Message(role="system", content=self.system_prompt))
            messages.extend(self.history)
            chat_response = self.client.chat(
                msgs=messages, tools=self.tool_registry.get_all_tools()
            )
            if chat_response.tool_calls:
                self.history.append(
                    Message(
                        role="assistant",
                        tool_calls=[
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.name,
                                    "arguments": json.dumps(tool_call.arguments),
                                },
                            }
                            for tool_call in chat_response.tool_calls
                        ],
                    )
                )
                for tool_call in chat_response.tool_calls:
                    res = self.tool_registry.execute(
                        tool_call.name, **tool_call.arguments
                    )
                    self.history.append(
                        Message(role="tool", content=res, tool_call_id=tool_call.id)
                    )

            else:
                self.history.append(
                    Message(role="assistant", content=chat_response.content)
                )
                return chat_response.content
