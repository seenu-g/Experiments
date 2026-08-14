from langchain.messages import HumanMessage

from graph import build_agent


def main():
    agent = build_agent()
    while True:
        user_input = input("Enter a calculation (or 'exit'/'quit'): ")
        if user_input.strip().lower() in ("exit", "quit"):
            break
        messages = [HumanMessage(content=user_input)]
        result = agent.invoke({"messages": messages})
        for m in result["messages"]:
            m.pretty_print()


if __name__ == "__main__":
    main()
