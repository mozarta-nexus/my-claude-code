import os

from agent.Agent import Agent
from agent.llm.base import LLMClient
from agent.tools.file.glob import GlobFile
from agent.tools.file.read import ReadFile
from agent.tools.file.write import WriteFile
from agent.tools.registry import ToolRegistry

WORK_DIR = os.getcwd()
SYSTEM = f"""
    你叫小帅，是一个AI编程助手，工作在{WORK_DIR}
"""

if __name__ == '__main__':

    tool_registry = ToolRegistry()
    tool_registry.register(ReadFile(root_dir=WORK_DIR))
    tool_registry.register(WriteFile(root_dir=WORK_DIR))
    tool_registry.register(GlobFile(root_dir=WORK_DIR))

    client = LLMClient()
    agent = Agent(client=client, system_prompt=SYSTEM,tool_registry=tool_registry)

    while True:
        user_input = input("User> ")
        if not user_input:
            continue
        if user_input.strip().lower() in ("exit", "quit", "q"):
            print("Bye!")
            break
        res= agent.run(user_input)
        print(f"AI> {res}")
