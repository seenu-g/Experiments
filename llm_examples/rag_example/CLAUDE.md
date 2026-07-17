# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Single-file educational example (`simple_rag.py`) demonstrating a minimal Retrieval-Augmented Generation (RAG) pipeline built with LangChain, FAISS, and LangGraph. No build system, package manifest, or test suite — this is a standalone script meant to be read and run directly.

## Running

```bash
pip install langchain langchain-community langchain-openai langchain-ollama langchain-anthropic langgraph faiss-cpu pypdf

# Pick a provider (defaults to "ollama" if unset):
export LLM_PROVIDER=ollama    # local, no API key; requires `ollama pull llama3.2` + `ollama pull nomic-embed-text`
# export LLM_PROVIDER=openai  # requires OPENAI_API_KEY
# export LLM_PROVIDER=claude  # requires ANTHROPIC_API_KEY (embeddings still use local Ollama)

python simple_rag.py
```

The `__main__` block runs a self-contained smoke test using two in-memory mock `Document` objects (no external files needed) and asks one sample question.

## Architecture

The script implements a two-node LangGraph pipeline over shared `RAGState` (`question`, `context`, `answer`):

1. **Provider selection** (`get_llm`, `get_embeddings`): `LLM_PROVIDER` env var (`ollama` default, `openai`, or `claude`) picks the chat model — `ChatOllama`, `ChatOpenAI`, or `ChatAnthropic`. Anthropic has no embeddings API, so `claude` mode reuses local `OllamaEmbeddings`; only `openai` mode uses `OpenAIEmbeddings`. Model names and the Ollama base URL are overridable via `OLLAMA_CHAT_MODEL`, `OLLAMA_EMBED_MODEL`, `OLLAMA_BASE_URL`, `OPENAI_CHAT_MODEL`, `CLAUDE_CHAT_MODEL`.
2. **Ingestion** (`chunk_documents` → `create_vector_store`): splits input `Document`s via `RecursiveCharacterTextSplitter` (1000 char chunks, 200 overlap), embeds them via `get_embeddings()`, and stores vectors in an in-memory FAISS index (module-level `vector_store` global).
3. **Graph nodes** (`retrieve_node` → `generate_node`): `retrieve_node` does a top-3 similarity search against `vector_store` and appends results to `state["context"]`; `generate_node` feeds the joined context + question into a `ChatPromptTemplate` piped to `get_llm()` (temperature 0) and writes the response into `state["answer"]`.
4. **Graph assembly** (`build_rag_graph`): wires `retrieve` → `generate` → `END` via `StateGraph`, compiled into the module-level `rag_app` global.
5. **Entry points**: `ask_question(question)` invokes the compiled graph for a single query; `complete_rag_pipeline(documents, questions)` runs the full lifecycle (chunk → embed/store → build graph → loop over questions).

State, vector store, and compiled graph are all held in module-level globals (`vector_store`, `rag_app`) rather than passed explicitly — keep this in mind when extending the script (e.g., adding multiple concurrent pipelines would require refactoring away from globals).

1. Receive the question.
2. Convert the question into an embedding.
3. Search the vector database.
4. Retrieve the most relevant chunks.
5. Build a prompt using those chunks.
6. Send the prompt to GPT.
7. Return the generated answer.
The LLM never searches documents directly.
