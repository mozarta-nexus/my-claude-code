import json
import time
from typing import Callable, Generator

from agent.data import Message
from agent.events import Event, ThinkingEvent, StreamEvent, ToolCallEvent, ToolResultEvent
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
        self._listeners: list[Callable[[Event], None]] = []

    def on(self, callback: Callable[[Event], None]):
        self._listeners.append(callback)

    def _emit(self, event: Event):
        for cb in self._listeners:
            cb(event)

    def _run_loop(self, user_input: str) -> Generator[Event, None, None]:
        self.history.append(Message(role="user", content=user_input))
        while True:
            messages = []
            if self.system_prompt:
                messages.append(Message(role="system", content=self.system_prompt))
            messages.extend(self.history)

            yield ThinkingEvent()

            full_content = ""
            tool_calls = None

            for chunk in self.client.chat_stream(msgs=messages, tools=self.tool_registry.get_all_tools()):
                if chunk.content:
                    full_content += chunk.content
                    yield StreamEvent(token=chunk.content)
                if chunk.tool_calls is not None:
                    tool_calls = chunk.tool_calls
            if tool_calls:
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
                            for tool_call in tool_calls
                        ],
                    )
                )
                for tool_call in tool_calls:
                    yield ToolCallEvent(name=tool_call.name, arguments=tool_call.arguments)

                    start = time.monotonic()
                    result = self.tool_registry.execute(tool_call.name, **tool_call.arguments)
                    duration = time.monotonic() - start
                    yield ToolResultEvent(name=tool_call.name, result=result, duration=duration)
                    self.history.append(
                        Message(role="tool", content=result, tool_call_id=tool_call.id)
                    )
            else:
                self.history.append(
                    Message(role="assistant", content=full_content)
                )
                return

    def run(self, user_input: str) -> Generator[Event, None, None]:
        for event in self._run_loop(user_input):
            self._emit(event)
            yield event