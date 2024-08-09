## DeepSeek API

This is a low level API for setting up agents. The agents needs DockerVM, and DeepSeek API to be working.

### Installation

1) Install local python packages
```bash
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

2) Install Docker container
``` bash
$ docker-compose up --build
```


3) Test the installation
```bash
$ python main.py
```

## Random

To manually connect to the docker container
``` bash
$ ssh python@localhost -p 2222
```

To remove the container
``` bash
$ docker-compose down
```

## Demo
```python
import DeepSeek

def main():
    answer, usage, trace = DeepSeek.simple_agent_v01("9.11 and 9.9 -- Which is bigger?")
    print(f"Answer: {answer}")
    print(f"Usage: {usage}")
    #print(f"Trace: {trace}")

if __name__ == "__main__":
    main()
```

Output:
```python
Answer: SOLVED: 9.9 is larger than 9.11.
Usage: {'input': 2645, 'output': 486, 'cost': 0.069}
```

Note, the cost is the total cost of running the agent in cents $.

## Changes
[x] Updated DockerScript to setup temfs for the agent.

[x] Add support for GPT-4o-mini. DeepSeek tends to have problem with function calling. For now this is a workaround.
