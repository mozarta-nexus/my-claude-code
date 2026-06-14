import json
import os
from dataclasses import dataclass
from typing import Generator

from dotenv import load_dotenv
from openai import OpenAI

from agent.data import Message, ChatResponse, ToolCallInfo

load_dotenv()


@dataclass
class StreamChunk:
    content: str | None = None
    tool_calls: list[ToolCallInfo] | None = None
    finish_reason: str | None = None


class LLMClient:
    def __init__(
            self,
            model: str | None = None,
            base_url: str | None = None,
            api_key: str | None = None,
            **kwargs,
    ):
        self.model = model or os.environ.get("MODEL")
        self.client = OpenAI(
            base_url=base_url or os.environ.get("BASE_URL"),
            api_key=api_key or os.environ.get("API_KEY"),
        )
        self.max_tokens = kwargs.get("max_tokens", 8000)

    def chat_stream(self, msgs: list[Message], tools: list | None = None) -> Generator[StreamChunk]:
        messages = [m.to_msg() for m in msgs]
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            max_tokens=self.max_tokens,
            stream=True,
        )

        content_buffer = ""
        tool_call_buffers: dict[int, dict] = {}
        for chunk in stream:
            choice = chunk.choices[0]
            delta = choice.delta
            if delta.content:
                content_buffer += delta.content
                yield StreamChunk(content=delta.content)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_call_buffers:
                        tool_call_buffers[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc.id:
                        tool_call_buffers[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_call_buffers[idx]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_call_buffers[idx]["arguments"] += tc.function.arguments

            if choice.finish_reason in ("tool_calls", "stop",):
                tool_calls = None
                if tool_call_buffers:
                    tool_calls = []
                    for idx in sorted(tool_call_buffers.keys()):
                        buf = tool_call_buffers[idx]
                        try:
                            arguments = json.loads(buf["arguments"])
                        except json.JSONDecodeError:
                            arguments = {"raw": buf["arguments"]}
                        tool_calls.append(ToolCallInfo(
                            id=buf["id"],
                            name=buf["name"],
                            arguments=arguments

                        ))
                yield StreamChunk(tool_calls=tool_calls, finish_reason=choice.finish_reason)

    def chat(self, msgs: list[Message], tools: list | None = None) -> ChatResponse:
        messages = [m.to_msg() for m in msgs]
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools, max_tokens=self.max_tokens
        )
        message = response.choices[0].message
        chat_response = ChatResponse()
        if message.tool_calls:
            tool_calls = []
            for tool_call in message.tool_calls:
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {"raw": tool_call.function.arguments}
                tool_calls.append(
                    ToolCallInfo(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=arguments,
                    )
                )
            chat_response.tool_calls = tool_calls

        if message.content:
            chat_response.content = message.content
        return chat_response
