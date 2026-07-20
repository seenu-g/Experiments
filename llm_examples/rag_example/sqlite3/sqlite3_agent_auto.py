"""
Autonomous multi-turn SQL agent (create_agent-based).

Unlike sqlite3_agent.py, which runs the six pipeline steps explicitly and prints
each one, this lets the model decide turn-by-turn which tool to call next. That
makes a mid-loop failure harder to localize, so only reach for this once
test_sqlite3_agent.py passes and you trust each individual step in isolation.
"""
from langchain.agents import create_agent

from sqlite3_agent import ensure_chinook_db
from sqlite3_helper import model, tools
from sqlite3_prompt import SQLAgentForLLM_prompt

ensure_chinook_db()

agent = create_agent(
    model,
    tools,
    system_prompt=SQLAgentForLLM_prompt,
)

question = "Which genre on average has the longest tracks?"

final_state = None
for step in agent.stream(
    {"messages": [{"role": "user", "content": question}]},
    stream_mode="values",
):
    final_state = step
    step["messages"][-1].pretty_print()
