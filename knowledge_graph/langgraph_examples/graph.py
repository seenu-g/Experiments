from typing import Literal

from langchain.messages import SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

from state import MessagesState
from tools import TOOLS, TOOLS_BY_NAME

MODEL_NAME = "llama3.1:latest"

SYSTEM_PROMPT = "You are a helpful assistant tasked with performing arithmetic on a set of inputs."


def build_agent():
    model = ChatOllama(model=MODEL_NAME, temperature=0)
    model_with_tools = model.bind_tools(TOOLS)

    def llm_call(state: MessagesState):
        """LLM decides whether to call a tool or not"""
        return {
            "messages": [
                model_with_tools.invoke(
                    [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
                )
            ],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }

    def tool_node(state: MessagesState):
        """Performs the tool call"""
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            selected_tool = TOOLS_BY_NAME[tool_call["name"]]
            observation = selected_tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
        return {"messages": result}

    def should_continue(state: MessagesState) -> Literal["tool_node", END]:
        """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tool_node"
        return END

    agent_builder = StateGraph(MessagesState)
    agent_builder.add_node("llm_call", llm_call)
    agent_builder.add_node("tool_node", tool_node)

    agent_builder.add_edge(START, "llm_call")
    agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    agent_builder.add_edge("tool_node", "llm_call")

    return agent_builder.compile()
