from DeepSeek.IO import DeepSeek
import logging
from copy import deepcopy
from sudoku import Sudoku as Su

# Add your API key, or use the .env file
client = DeepSeek(api_key=None, use_OpenAI=True)


def simple_agent_v01(question: str):
    usage = {}
    messages = [
        {"role": "system", "content": """Solve the problem. Think step by step"""},
        {
            "role": "user",
            "content": """\
Rephrase the task.
Then make high-level observations.
Break the task into smaller steps.
Create only an initial plan.\n\n
"""
            + question,
        },
    ]

    out = client.infer_without_tools(messages, usage)

    N = 5
    for i in range(N):
        logging.info(f"Attempt {i+1} / {N}")

        # Run with the suggested approach from the reviewer
        messages += [{"role": "user", "content": "Solve the problem. Provide confidence level."}]
        out = client.infer_with_tools(messages, usage)

        logging.info("Generator: " + out)

        # check if the task is solved
        cmd = """If the task is solved, please type "SOLVED:" and the answer (the text after solved will be visible to user). \
            Make sure to be very critical if the task is solved in full. \
            Task is consider solved only if the answer contains ALL requirements to the original question. \
            Otherwise, type "NO". And suggest improvements, or different approaches."""

        messages += [{"role": "user", "content": cmd}]
        out = client.infer_with_tools(messages, usage)

        logging.info("Verifier: " + out)

        # terminate the loop if the task is solved
        if "SOLVED:" in out:
            # display only the answer
            return out, usage, messages

    return "Unable to solve the problem", usage, messages
