import sys
import uuid
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from rich import print

sys.stdout.reconfigure(encoding="utf-8")

llm = ChatOllama(model='phi4-mini', temperature=0.7)

def call_llm(prompt: str, system_message: str) -> str:
    response = llm.invoke([SystemMessage(system_message), HumanMessage(prompt)])
    return response.content

class PromptState(TypedDict):
    original_prompt: str
    improved_prompt: Optional[str]
    final_prompt: Optional[str]
    final_answer: Optional[str]
    step: str

def improve_prompt_node(state: PromptState) -> PromptState:
    print(f"🤖 Improving prompt with Ollama: {state['original_prompt']}")

    system_message = """You are a prompt engineering expert. Your goal is to take the user's original prompt and improve it for clarity, specificity, and effectiveness when used with an LLM. Make it more detailed, add context if needed, and ensure it's optimized for generating high-quality responses. Return only the improved prompt, no explanations."""

    improved_prompt = call_llm(state['original_prompt'], system_message)

    return {
        **state,
        "improved_prompt": improved_prompt,
        "step": "prompt_improved"
    }

def human_review_node(state: PromptState) -> PromptState:
    print("👤 Requesting human review...")

    human_response = interrupt({
        "task": "Please review and edit the improved prompt if needed",
        "original_prompt": state["original_prompt"],
        "improved_prompt": state["improved_prompt"]
    })

    # Either accept or edit the improved prompt
    final_prompt = human_response.get("edited_prompt", state["improved_prompt"])

    return {
        **state,
        "final_prompt": final_prompt,
        "step": "human_reviewed"
    }

def answer_prompt_node(state: PromptState) -> PromptState:
    print(f"🤖 Generating final answer with Ollama for: {state['final_prompt']}")

    system_message = """You are a helpful AI assistant. Provide a comprehensive answer to the user's prompt, drawing on accurate knowledge and clear explanations. Structure your response logically with sections if appropriate."""

    final_answer = call_llm(state['final_prompt'], system_message)

    return {
        **state,
        "final_answer": final_answer,
        "step": "completed"
    }

def create_app():
    builder = StateGraph(PromptState)

    builder.add_node("improve_prompt", improve_prompt_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("answer_prompt", answer_prompt_node)

    builder.add_edge(START, "improve_prompt")
    builder.add_edge("improve_prompt", "human_review")
    builder.add_edge("human_review", "answer_prompt")
    builder.add_edge("answer_prompt", END)

    return builder.compile(checkpointer=InMemorySaver())

def main():
    app = create_app()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    user_prompt = input("Enter your prompt: ").strip() or "Tell me about machine learning"

    initial_state = {"original_prompt": user_prompt, "step": "starting"}

    print(f"🚀 Processing with Ollama: {user_prompt}")
    result = app.invoke(initial_state, config=config)

    while "__interrupt__" in result:
        human_response = {"edited_prompt": input("Edit prompt (or Enter to approve): ")}
        result = app.invoke(Command(resume=human_response), config=config)

    print(f"Final prompt: {result['final_prompt']}")
    print(f"🎯 Answer:\n{result['final_answer']}")