from abc import abstractmethod, ABC

TAG = "\033[44m"
RESET = "\033[0m"
MAX_RESULT_LEN = 200


class Tool(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass


    @property
    @abstractmethod
    def description(self) -> str:
        pass


    @property
    @abstractmethod
    def parameters(self) -> dict:
        pass

    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def _print_call(self, **kwargs):
        args_str = " ".join(str(v) for v in kwargs.values())
        print(f"  {TAG}[{self.name}]{RESET} {args_str}")

    def _print_result(self, result: str):
        display = result[:MAX_RESULT_LEN]
        if len(result) > MAX_RESULT_LEN:
            display += "..."
        print(f"  {TAG}[{self.name} result]{RESET} {display}")

    @abstractmethod
    def execute(self, **kwargs) -> str:
        pass
