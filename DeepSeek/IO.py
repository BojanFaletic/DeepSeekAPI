import os
import inspect
import json
import logging
import time

from openai import Client, RateLimitError
from openai.types.chat import ChatCompletion, ChatCompletionMessageToolCall

from dotenv import load_dotenv

from .network import Socket

load_dotenv()


class DeepSeek:
    def __init__(self, api_key=None, use_OpenAI=False) -> None:
        if use_OpenAI:
            MODEL_URL = "https://api.openai.com/v1"
            api_key = os.getenv("OPENAI_KEY") if api_key is None else api_key
            self.default_model = {"name": "gpt-4o-mini", "input": 0.15, "output": 0.6}

        else:
            MODEL_URL = "https://api.deepseek.com/beta"
            api_key = os.getenv("DEEPSEEK_KEY") if api_key is None else api_key
            self.default_model = {"name": "deepseek-chat", "input": 0.14, "output": 0.28}

        if api_key is None:
            raise ValueError("API key not found. Please provide an API key or add it to the .env file")

        self.client = Client(base_url=MODEL_URL, api_key=api_key)

        # SSH connection to remote server
        self.socket = Socket()
        self.log_file = "deepseek_code.log"

        # list of functions that can be called by the model
        self.init_model_tools(
            [
                self.socket.run_bash_shell,
                self.socket.run_python_shell,
                # search,
            ]
        )

        self.init_log_file()

    def init_log_file(self) -> None:
        with open(self.log_file, "w") as f:
            f.write("")

    def init_model_tools(self, functions: list) -> None:
        self.functions = functions
        self.tools = self.__make_tools(functions)

    def __make_tools(self, functions: list) -> list:
        tools = []

        for func in functions:
            tool = {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": func.__doc__,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }

            # Inspect the function signature to get parameters
            sig = inspect.signature(func)
            for param_name, param in sig.parameters.items():
                tool["function"]["parameters"]["properties"][param_name] = {
                    "type": "string",  # You might want to infer the type if possible
                    "description": f"Parameter: {param_name}",
                }
                if param.default == inspect.Parameter.empty:
                    tool["function"]["parameters"]["required"].append(param_name)

            tools.append(tool)

        return tools

    def __handle_tool_call(self, tool_call: ChatCompletionMessageToolCall, messages: list) -> list:
        tool_call_function = tool_call.function
        tool_call_arguments: dict = json.loads(tool_call_function.arguments)
        tool_call_name = tool_call_function.name

        function_names = [func.__name__ for func in self.functions]
        if tool_call_name in function_names:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"Tool call: {tool_call_name}\n")
                for key, value in tool_call_arguments.items():
                    f.write(f"{key}: {value}\n")
                    f.write("\n")
                f.write("\n\n")

            # Call the function
            f_ptr = function_names.index(tool_call_name)
            output = self.functions[f_ptr](**tool_call_arguments)

            if len(output) == 0:
                # sometimes the output is empty (e.g. when there is no error or stdout)
                output = "Warning: There was no output from stdout. Did you forget to print?"
            elif len(output) > 1000:
                # sometimes the output is too long
                logging.warn("Output is too long. Trimming the output")
                output = output[:1000]
                output += "\n\nWarning: Output was trimmed because it was too long (more than 1000 characters)."

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"Output: {output}\n")
                f.write("-" * 80)
                f.write("\n\n")

            messages += [{"role": "tool", "tool_call_id": tool_call.id, "content": output}]
        else:
            raise ValueError(f"Unknown tool call: {tool_call_name}")

        return messages

    def infer_with_tools(self, messages: list, prev_usage=None) -> tuple:
        try:
            response: ChatCompletion = self.client.chat.completions.create(
                model=self.default_model["name"],
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
            )
        except RateLimitError as e:
            # Most likely is rate limit per minute. It could be some other error (TODO: check the error code)
            logging.warn(f"Rate limit error: {e}. Sleeping for 60 seconds")
            time.sleep(60)
            return self.infer_with_tools(messages, prev_usage=prev_usage)

        usage = {
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
        }

        # Add the usage of the previous call
        if prev_usage is not None:
            usage["input"] += prev_usage["input"]
            usage["output"] += prev_usage["output"]

        cost = (self.default_model["input"], self.default_model["output"])
        usage["cost"] = round((usage["input"] * cost[0] + usage["output"] * cost[1]) / 1e4, 3)

        for choice in response.choices:
            if choice.message.tool_calls:
                messages.append(choice.message)
                for tool_call in choice.message.tool_calls:
                    messages = self.__handle_tool_call(tool_call, messages)
                return self.infer_with_tools(messages, prev_usage=usage)

        content = "\n".join([choice.message.content for choice in response.choices])
        messages.append({"role": "assistant", "content": content})
        return content, usage, messages
