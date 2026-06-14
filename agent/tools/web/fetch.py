import httpx

from agent.tools.base import Tool, TAG, RESET


class WebFetch(Tool):
    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "获取指定URL的网页内容，返回文本或Markdown格式"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "要获取的网页URL"},
                "max_length": {
                    "type": "integer",
                    "description": "返回内容的最大字符数，默认5000",
                },
            },
            "required": ["url"],
        }

    def _print_call(self, **kwargs):
        print(f"{TAG}[{self.name}]{RESET} {kwargs.get('url', '')}")

    def execute(self, **kwargs) -> str:
        url = kwargs.get("url")
        max_length = kwargs.get("max_length", 5000)
        if not url:
            raise ValueError("url is required")
        self._print_call(**kwargs)
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        result = response.text
        if len(result) > max_length:
            result = result[:max_length] + "\n... (truncated)"
        self._print_result(result)
        return result
