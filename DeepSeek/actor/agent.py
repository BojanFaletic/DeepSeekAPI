from typing import Optional
from DeepSeek.IO import DeepSeek


class BaseAgent:
    def __init__(self, client: Optional[DeepSeek] = None) -> None:
        if client is None:
            client = DeepSeek(use_OpenAI=True)
        self.client = client

        # Initialize memory
        self.init_system_prompt("")
        self.init_messages([])

    def init_system_prompt(self, system_prompt: str) -> None:
        self.__system_prompt = system_prompt

    def init_messages(self, messages: list) -> None:
        self.__messages = messages

    def __infer_stateless(self, query: str, usage: Optional[dict] = None) -> str:
        messages = [
            {"role": "system", "content": self.__system_prompt},
            {"role": "user", "content": query},
        ]
        return self.client.infer_with_tools(messages, usage)

    def turning_complete_evaluator(self, query: str, usage: Optional[dict] = None) -> str:
        return self.__infer_stateless(query, usage)

class Verify(BaseAgent):
    def __init__(self, client: Optional[DeepSeek] = None) -> None:
        super().__init__(client)

        # list of tools that agent can use
        self.client.init_model_tools([self.client.socket.run_python_code])

        self.init_system_prompt(
            """\
You must verify the solution. Use python to get definitive answers. \
You must print(result) to see the output.
example:
x = 1
x # Warning: does not print anything
print(x) # this will return 1
"""
        )

