import base64
import warnings

from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

import paramiko
from paramiko.ssh_exception import NoValidConnectionsError
from duckduckgo_search import DDGS


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
                hostname=host, port=port, username=username, password=password, timeout=10
            )
        except NoValidConnectionsError as e:
            raise ValueError(f"Check if docker runs. Error: {e}")

    def __del__(self):
        self.client.close()

    def run_bash_shell(self, command: str) -> str:
        """
        Run a bash command in the remote server.

        @param command: Bash command to be executed in the remote server.
        @return: stdout of the bash command execution.
        """
        # Run the command on the remote server
        stdin, stdout, stderr = self.client.exec_command(command)

        # Check for errors
        error = stderr.read().decode("utf-8")
        if error:
            return f"Error: {error}"

        # Return the output
        return stdout.read().decode("utf-8")

    def run_python_code(self, code: str) -> str:
        """
        Run python code in the remote server. In order to see the output you must print it!

        @param code: Python code to be executed in the remote server.
        @return: stdout of the python code execution.
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
