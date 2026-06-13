import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_URL = os.environ.get("BASE_URL")
API_KEY = os.environ.get("API_KEY")
MODEL = os.environ.get("MODEL")

WORK_DIR = os.getcwd()

SYSTEM = f"""
你叫小帅，是一个编程助手，工作在{WORK_DIR}
"""

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)


def ai_msg(content: str) -> dict[str, str]:
    return build_msg(content)


def sys_msg(content) -> dict[str, str]:
    return build_msg(content, "system")


def user_msg(content: str) -> dict[str, str]:
    return build_msg(content)


def build_msg(content: str, role="user") -> dict[str, str]:
    return {"role": role, "content": content}


def run(messages: list):
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=8000,
            stream=True
        )
        parts = []
        print("\nAI>", end="")
        for chunk in response:
            delta_content = chunk.choices[0].delta.content
            if delta_content:
                print(f"{delta_content}", end="", flush=True)
                parts.append(delta_content)
        print()
        messages.append(ai_msg("".join(parts)))
        break


if __name__ == '__main__':
    messages = [sys_msg(SYSTEM)]
    while True:
        user_input = input("You> ")
        if not user_input:
            continue
        if user_input.strip().lower() in ("exit", "quit", "q"):
            print("Bye!")
            break
        messages.append(user_msg(user_input))
        run(messages)
