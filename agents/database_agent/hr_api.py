"""
hr_api.py — FastAPI server for the HR Agent.

Endpoints:
  POST /chat          — single-turn question → JSON answer
  POST /chat/stream   — streaming response (Server-Sent Events)
  POST /reset         — clear conversation history
  GET  /health        — liveness check
  GET  /docs          — Swagger UI (auto-generated)

Run:
  uvicorn hr_api:app --reload --port 8000

Then open: http://localhost:8000/docs
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from hr_agent import HRAgent, MODEL

# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="HR Agent API",
    description="Natural language interface to the HR PostgreSQL database, powered by Ollama + Hermes.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    tool_calls_made: list[str] = []

class ResetRequest(BaseModel):
    session_id: str = "default"

# ── Session store (in-memory; use Redis for production) ───────────────────────
# One HRAgent per session: same loop, prompt and code-enforced disable confirmation as the CLI.
# A disable request is answered with a question; the session's next message "yes" performs it.

sessions: dict[str, HRAgent] = {}


def get_agent(session_id: str) -> HRAgent:
    if session_id not in sessions:
        sessions[session_id] = HRAgent(name=f"hr-agent:{session_id}")
    return sessions[session_id]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "model": MODEL}


@app.post("/reset", tags=["Session"])
def reset_session(req: ResetRequest):
    sessions.pop(req.session_id, None)             # also drops any pending disable request
    return {"message": f"Session '{req.session_id}' cleared."}


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
def chat(req: ChatRequest):
    """
    Send a natural-language question to the HR agent.
    Returns a complete answer (non-streaming).

    Example questions:
    - "List all managers"
    - "What is the salary of managers in Engineering?"
    - "Show me the education of employees in the Data department"
    - "Disable employee John Smith"
    """
    agent = get_agent(req.session_id)
    answer, tools = "", []
    try:
        for event in agent.steps(req.message):
            if event["type"] == "tool":
                tools.append(event["name"])
            elif event["type"] == "answer":
                answer = event["data"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        answer=answer,
        session_id=req.session_id,
        tool_calls_made=tools,
    )


@app.post("/chat/stream", tags=["Agent"])
def chat_stream(req: ChatRequest):
    """
    Streaming version — emits Server-Sent Events.
    Each event is a JSON object: {"type": "tool"|"chunk"|"done", "data": "..."}

    Connect with EventSource in the browser or requests in Python.
    """
    agent = get_agent(req.session_id)

    def generate():
        for event in agent.steps(req.message):
            if event["type"] == "tool":
                yield f"data: {json.dumps({'type': 'tool', 'data': 'Calling ' + event['name'] + '...'})}\n\n"
            elif event["type"] == "answer":
                # Stream word-by-word for a live feel
                for word in event["data"].split(" "):
                    yield f"data: {json.dumps({'type': 'chunk', 'data': word + ' '})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'data': ''})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/sessions", tags=["Session"])
def list_sessions():
    return {
        "sessions": [
            {"session_id": sid, "turns": sum(1 for m in a.history if m.get("role") == "user")}
            for sid, a in sessions.items()
        ]
    }
