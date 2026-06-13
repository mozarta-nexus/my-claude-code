import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from agent.data import Message, ChatResponse, ToolCallInfo

load_dotenv()


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

    def chat(self, msgs: list[Message], tools: list | None = None) -> ChatResponse:
        messages = [
            m.to_msg() for m in msgs
        ]
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools, max_tokens=self.max_tokens
        )
        message = response.choices[0].message
        chat_response = ChatResponse()
        if message.tool_calls:
            tool_calls = []
            for tool_call in message.tool_calls:
                tool_calls.append(ToolCallInfo(id=tool_call.id, name=tool_call.function.name,
                                               arguments=json.loads(tool_call.function.arguments)))
            chat_response.tool_calls = tool_calls

        if message.content:
            chat_response.content = message.content
        return chat_response
