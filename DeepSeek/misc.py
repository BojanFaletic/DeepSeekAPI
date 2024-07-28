from DeepSeek.IO import DeepSeek
import logging
from copy import deepcopy
from sudoku import Sudoku as Su

# Add your API key, or use the .env file
client = DeepSeek(api_key=None, use_OpenAI=True)


def simple_agent_v01(question: str):
    system = [{"role": "system", "content": "You must solve the problem. Think step by step"}]
    out, usage, trace = client.infer_with_tools(system + [{"role": "user", "content": question}])

    N = 5
    for i in range(N):
        logging.info(f"Attempt {i+1} / {N}")

        # check if the task is solved
        cmd = "Is the task complete? If yes, write 'SOLVED:' flowed by the full answer. If no, briefly describe the issue and suggest improvements."
        out, usage, trace = client.infer_with_tools(
            messages=trace + [{"role": "user", "content": cmd}], prev_usage=usage
        )

        logging.info(out)

        # terminate the loop if the task is solved
        if "SOLVED:" in out:
            # trim the output
            out = out.replace("SOLVED:", "").strip()
            return out, usage, trace

        # suggest a new approach
        out, usage, trace = client.infer_with_tools(
            messages=trace + [{"role": "user", "content": "give it another try"}],
            prev_usage=usage,
        )

    return "Unable to solve the problem", usage, trace


def simple_agent_v02(question: str):
    system = [
        {
            "role": "system",
            "content": """\
1. **Solve the problem.**
2. **Rephrase the question.**
3. **Make high-level observations.**
4. **Create an initial plan.**
5. **Break the plan into smaller steps.**
6. **Verify each step.**
7. **Think step by step and stay calm.**""",
        }
    ]

    out, usage, trace = client.infer_with_tools(system + [{"role": "user", "content": question}])

    N = 5
    for i in range(N):
        logging.info(f"Attempt {i+1} / {N}")

        # check if the task is solved
        cmd = """If the task is solved, please type "SOLVED:" and the answer. \
            Make sure to be very critical if the task is solved in full. \
            Task is consider solved only if the answer contains ALL requirements to the original question. \
            Otherwise, type "NO". And suggest improvements, or different approaches."""

        out, usage, trace = client.infer_with_tools(
            messages=trace + [{"role": "user", "content": cmd}], prev_usage=usage
        )

        logging.info(out)

        # terminate the loop if the task is solved
        if "SOLVED:" in out:

            # display only the answer
            return out, usage, trace

        # Run with the suggested approach from the reviewer
        out, usage, trace = client.infer_with_tools(
            messages=trace,
            prev_usage=usage,
        )

    return "Unable to solve the problem", usage, trace

def simple_agent_v03(question: str):
    system = [
        {
            "role": "system",
            "content": """\
Solve the problem.
Rephrase the question.
Think step by step""",
        }
    ]

    cmd = """\
Rephrase the task.
This is your planning step.
Then make high-level observations.
Break the task into smaller steps.
Create only an initial plan.
"""

    out, usage, trace = client.infer_with_tools(
        system + [{"role": "user", "content": cmd + question}]
    )

    N = 5
    for i in range(N):
        logging.info(f"Attempt {i+1} / {N}")

        # Run with the suggested aproach from the reviewer
        out, usage, trace = client.infer_with_tools(
            messages=trace + [{"role": "user", "content": "Solve the problem."}], prev_usage=usage
        )

        logging.info("Generator: " + out)

        # check if the task is solved
        cmd = """If the task is solved, please type "SOLVED:" and the answer (the text after solvedd will be visible to user). \
            Make sure to be very critical if the task is solved in full. \
            Task is consider solved only if the answer contains ALL requirements to the original question. \
            Otherwise, type "NO". And suggest improvements, or different approaches."""

        out, usage, trace = client.infer_with_tools(
            messages=trace + [{"role": "user", "content": cmd}], prev_usage=usage
        )

        logging.info("Verifier: " + out)

        # terminate the loop if the task is solved
        if "SOLVED:" in out:
            # display only the answer
            return out, usage, trace

    return "Unable to solve the problem", usage, trace


