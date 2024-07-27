import os
import json
import inspect
import base64
import warnings

from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

from openai import Client
from openai.types.chat import ChatCompletion
from openai.types.chat import ChatCompletionMessageToolCall
from dotenv import load_dotenv
from duckduckgo_search import DDGS

import paramiko
from paramiko.ssh_exception import NoValidConnectionsError
load_dotenv()


class DeepSeek:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.getenv("DEEPSEEK_KEY")
            if api_key is None:
                raise ValueError(
                    "API key not found. Please provide an API key or add it to the .env file"
                )

        DEEPSEEK_URL = "https://api.deepseek.com/beta"
        self.client = Client(base_url=DEEPSEEK_URL, api_key=api_key)

        self.socket = Socket()
        self.log_file = "deepseek_code.log"

        with open(self.log_file, "w") as f:
            f.write("")

        self.functions = [
            self.socket.run_bash_shell,
            self.socket.run_python_shell,
            search,
        ]
        self.tools = self.__make_tools(self.functions)

    def infer(self, messages, model="deepseek-coder"):
        response: ChatCompletion = self.client.chat.completions.create(
            model=model, messages=messages, response_format={"type": "json_object"}
        )

        usage = {
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
        }
        usage["cost"] = round(usage["input"] * 0.14 + usage["output"] * 0.28 / 1e4, 3)
        content = response.choices[0].message.content
        try:
            json_content = json.loads(content)
        except:
            raise ValueError("Invalid JSON response from DeepSeek")

        return json_content, usage

    def __make_tools(self, functions: list):
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

    def __handle_tool_call(self, tool_call: ChatCompletionMessageToolCall, messages):
        tool_call_id = tool_call.id
        tool_call_function = tool_call.function
        tool_call_arguments = json.loads(tool_call_function.arguments)
        tool_call_name = tool_call_function.name

        function_names = [func.__name__ for func in self.functions]
        if tool_call_name in function_names:
            f_ptr = function_names.index(tool_call_name)

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"Tool call: {tool_call_name}\n")
                for key, value in tool_call_arguments.items():
                    f.write(f"{key}: {value}\n")
                    f.write("\n")
                f.write("\n\n")

            output = self.functions[f_ptr](**tool_call_arguments)
            if len(output) == 0:
                output = "Warning: There was no output from stdout"

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"Output: {output}\n")
                f.write("-" * 80)
                f.write("\n\n")

            messages += [
                {"role": "tool", "tool_call_id": tool_call_id, "content": output}
            ]
        else:
            raise ValueError(f"Unknown tool call: {tool_call_name}")

        return messages

    def infer_with_tools(self, messages: list, model="deepseek-coder", prev_usage=None):
        response: ChatCompletion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto",
        )

        usage = {
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
        }

        # Add the usage of the previous call
        if prev_usage is not None:
            usage["input"] += prev_usage["input"]
            usage["output"] += prev_usage["output"]

        usage["cost"] = round((usage["input"] * 0.14 + usage["output"] * 0.28) / 1e4, 3)

        if response.choices[0].finish_reason == "tool_calls":
            # add the output of the tool to the messages (this is a bug!! on the deepSeek side)
            messages.append(response.choices[0].message)
            for tool_call in response.choices[0].message.tool_calls:
                messages = self.__handle_tool_call(tool_call, messages)
            return self.infer_with_tools(messages, model=model, prev_usage=usage)

        content = response.choices[0].message.content
        messages.append({"role": "assistant", "content": content})
        return content, usage, messages


class Socket:
    def __init__(self, host=None, port=None, username=None, password=None):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if not (host or port or username or password):
            port = 2222
            username = "python"
            password = "python"

        try:
            self.client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=10,
            )
        except NoValidConnectionsError as e:
            raise ValueError(f"Check if docker runs. Error: {e}")

    def __del__(self):
        self.client.close()

    def run_bash_shell(self, command: str) -> str:
        """Run a bash command in the remote server.
        Args:
            command (str): Bash command to be executed in the remote server.
        Returns:
            str: Output of the command execution.
        """
        # Run the command on the remote server
        stdin, stdout, stderr = self.client.exec_command(command)

        # Check for errors
        error = stderr.read().decode("utf-8")
        if error:
            return f"Error: {error}"

        # Return the output
        return stdout.read().decode("utf-8")

    def run_python_shell(self, code: str) -> str:
        """Run python code in the remote server.
        Args:
            code (str): Python code to be executed in the remote server.
        Returns:
            str: Output of the code execution.
        """
        # Encode the Python code in base64
        encoded_code = base64.b64encode(code.encode()).decode()

        # Command to decode and execute the Python code
        command = f"python3 -c \"import base64; exec(base64.b64decode('{encoded_code}').decode())\""

        # Run the command on the remote server
        stdin, stdout, stderr = self.client.exec_command(command)

        # Check for errors
        error = stderr.read().decode("utf-8")
        if error:
            return f"Error: {error}"

        # Return the output
        return stdout.read().decode("utf-8")


def search(query: str) -> str:
    """Searches the web for the query and returns the top 4 results
    Args:
        query (str): The search query
    Returns:
        str: The top 4 search results
    """
    results = DDGS().text(query, max_results=4)

    # serialize the results to text
    str_results = ""
    for item in results:
        str_results += f"{item['title']}\n{item['href']}\n{item['body']}\n\n"
    return str_results
