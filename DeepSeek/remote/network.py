from shlex import quote as shlex_quote
import warnings

from cryptography.utils import CryptographyDeprecationWarning

warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

import paramiko
from paramiko.ssh_exception import NoValidConnectionsError
from paramiko.channel import ChannelStdinFile, ChannelFile, ChannelStderrFile
from duckduckgo_search import DDGS


class Socket:
    TEMPFS_DIR = "/mnt/tempfs"

    def __init__(self, host=None, port=None, username=None, password=None):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if not (host or port or username or password):
            # Defined in the docker-compose file
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

    def __execute(
        self, command: str, timeout: int = 3
    ) -> tuple[ChannelStdinFile, ChannelFile, ChannelStderrFile]:
        watchdog = lambda cmd: f"timeout {timeout}s {cmd} || kill -9 $!"
        change_dir = lambda cmd: f"cd {self.TEMPFS_DIR} && {cmd}"

        cmd_str = change_dir(watchdog(command))
        return self.client.exec_command(cmd_str)

    def run_bash_shell(self, command: str) -> str:
        """
        Run a bash command in the remote server.

        @param command: Bash command to be executed in the remote server.
        @return: stdout of the bash command execution.
        """
        # Run the command on the remote server
        stdin, stdout, stderr = self.__execute(command)

        # If there is an error, return it, otherwise return the output
        error = stderr.read().decode("utf-8")
        if error:
            return f"Error: {error}"
        return stdout.read().decode("utf-8")

    def run_python_code(self, code: str) -> str:
        """
        Run python code in the remote server.
        Important: You MUST print everything you want to see in the output.

        @param code: Python code to be executed in the remote server.
        @return: stdout of the python code execution.
        """

        # Run the command on the remote server
        command = f"python3 -c {shlex_quote(code)}"
        stdin, stdout, stderr = self.__execute(command)

        # If there is an error, return it, otherwise return the output
        error = stderr.read().decode("utf-8")
        if error:
            return f"Error: {error}"
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
