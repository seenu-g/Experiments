import asyncio
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama
from langchain.agents import create_agent

MATH_SERVER_PATH = str(Path(__file__).resolve().parent / "math_server.py")

SYSTEM_PROMPT = (
    "You have access to tools. When a tool returns a result, state that result "
    "directly and plainly in your final answer. Do not say you are about to check "
    "something or describe what you are doing — just answer using the tool's output."
)
# Known limitation with llama3.1:latest: for the weather tool, the model sometimes
# hallucinates fabricated weather-API-shaped data instead of relaying the tool's
# actual (short, plain-string) result. Tightening this prompt further made it worse
# (longer fabrications), so this isn't reliably fixable via prompting alone with
# this model. The math tool grounds correctly and consistently.

async def main():
    client = MultiServerMCPClient(
        {
            "math": {
                "transport": "stdio",  # Local subprocess communication
                "command": "python",
                "args": [MATH_SERVER_PATH],
            },
            "weather": {
                "transport": "http",  # HTTP-based remote server
                # Ensure you start your weather server on port 8000
                "url": "http://localhost:8000/mcp",
            }
        }
    )

    tools = await client.get_tools()
    # Uses a local Ollama model, so this requires `ollama pull llama3.1` and Ollama running.
    agent = create_agent(
        ChatOllama(model="llama3.1:latest", temperature=0.7),
        tools,
        system_prompt=SYSTEM_PROMPT,
    )
    math_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
    )
    weather_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what is the weather in nyc?"}]}
    )
    print(math_response + "\n")
    print(weather_response + "\n")

if __name__ == "__main__":
    asyncio.run(main())