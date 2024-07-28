## DeepSeek API

This is a low level API for setting up agents. The agents needs DockerVM, and DeepSeek API to be working.

### Installation

1) Install Docker
2) Bring docker up via (Dockerfile and docker-compose.yml)
``` bash
$ docker-compose up
```
TODO: you need to make new user from which DeepSeek can connect.

4) Install python packages
```bash
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

5) Test the installation
```bash
$ python main.py
```


## Demo
```python
import DeepSeek

def main():
    answer, usage, trace = DeepSeek.simple_agent_v03("9.11 and 9.9 -- Which is bigger?")
    print(f"Answer: {answer}")
    print(f"Usage: {usage}")
    #print(f"Trace: {trace}")

if __name__ == "__main__":
    main()
```

Output:
```python
Answer: SOLVED: 9.9 is larger than 9.11.
Usage: {'input': 4083, 'output': 723, 'cost': 0.105}
```

Note, the cost is the total cost of running the agent in cents $.

## Changes

-- Add support for GPT-4o-mini. DeepSeek tends to have problem with function calling. For now this is a workaround.
