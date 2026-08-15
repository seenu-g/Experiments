import sys

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from rich import print

sys.stdout.reconfigure(encoding="utf-8")

llm = ChatOllama(model='phi4-mini', temperature=0.7)

IMPROVE_SYSTEM_MESSAGE = """You are a prompt engineering expert. Your goal is to take the user's original prompt and improve it for clarity, specificity, and effectiveness when used with an LLM. Make it more detailed, add context if needed, and ensure it's optimized for generating high-quality responses. Return only the improved prompt, no explanations."""

ANSWER_SYSTEM_MESSAGE = """You are a helpful AI assistant. Provide a comprehensive answer to the user's prompt, drawing on accurate knowledge and clear explanations. Structure your response logically with sections if appropriate."""

def call_llm(prompt: str, system_message: str) -> str:
    response = llm.invoke([SystemMessage(system_message), HumanMessage(prompt)])
    return response.content

def main():
    original_prompt = input("Enter your prompt: ").strip() or "Tell me about machine learning"

    print(f"🚀 Processing with Ollama: {original_prompt}")
    improved_prompt = call_llm(original_prompt, IMPROVE_SYSTEM_MESSAGE)

    print(f"👤 Improved prompt: {improved_prompt}")
    edited = input("Edit prompt (or Enter to approve): ").strip()
    final_prompt = edited or improved_prompt

    print(f"🤖 Generating final answer with Ollama for: {final_prompt}")
    final_answer = call_llm(final_prompt, ANSWER_SYSTEM_MESSAGE)

    print(f"Final prompt: {final_prompt}")
    print(f"🎯 Answer:\n{final_answer}")

if __name__ == "__main__":
    main()
