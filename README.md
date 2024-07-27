## DeepSeek API

This is a low level API for setting up agents. The agents needs DockerVM, and DeepSeek API to be working.

### Installation

1) Install Docker
2) Bring docker up via (Dockerfile and docker-compose.yml)
'''
docker-compose up
'''
TODO: you need to make new user from which DeepSeek can connect.

4) Install python packages
'''
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
'''

5) Test the installation
'''
python main.py
'''


## Demo
```python
import DeepSeek

def main():
    answer, usage, trace = DeepSeek.simple_agent_v02("9.11 and 9.9 -- Which is bigger? think")
    print(f"Answer: {answer}")
    print(f"Usage: {usage}")
    #print(f"Trace: {trace}")

if __name__ == "__main__":
    main()

```

Output:
```python
Answer: SOLVED: 9.9 is bigger than 9.11.
Usage: {'input': 1390, 'output': 234, 'cost': 0.026}
```

Note, the cost is the total cost of running the agent in cents $.