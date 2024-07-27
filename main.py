import DeepSeek

def main():
    answer, usage, trace = DeepSeek.simple_agent_v02("9.11 and 9.9 -- Which is bigger? think")
    print(f"Answer: {answer}")
    print(f"Usage: {usage}")
    #print(f"Trace: {trace}")

if __name__ == "__main__":
    main()
