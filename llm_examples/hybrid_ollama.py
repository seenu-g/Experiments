import argparse
import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from llama_cpp import Llama

def unload_ollama_vram():
    """Tells the running Ollama background daemon to clear its VRAM usage."""
    url = "http://localhost:11434/api/generate"
    # Sending an empty request with keep_alive: 0 drops all resident models from memory
    payload = json.dumps({
        "model": "", 
        "prompt": "", 
        "keep_alive": 0
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url, 
        data=payload, 
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        # Execute the network call silently
        with urllib.request.urlopen(req, timeout=3) as response:
            response.read()
        print("Ollama VRAM successfully cleared.")
    except Exception:
        # If the server isn't running, it means VRAM is already clear
        print("Ollama background server not responding. Assuming VRAM is clear.")

def load_ollama_model_natively(model_name="llama3", tag="latest", embedding=False):
    # 1. Clear out any models currently sitting in Ollama's VRAM pool
    unload_ollama_vram()
    
    # 2. Resolve local file paths
    base_dir = os.environ.get("OLLAMA_MODELS", os.path.expanduser("~/.ollama/models"))
    manifest_path = os.path.join(base_dir, "manifests", "registry.ollama.ai", "library", model_name, tag)
    
    # 3. Parse the manifest JSON to discover the model weight layer
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    model_digest = None
    for layer in manifest.get("layers", []):
        if layer.get("mediaType") == "application/vnd.ollama.image.model":
            model_digest = layer["digest"].replace(":", "-")
            break
            
    if not model_digest:
        raise FileNotFoundError(f"Could not find valid model weights in manifest for {model_name}")
        
    blob_path = os.path.join(base_dir, "blobs", model_digest)
    
    # 4. Load the file weights natively into your application process via C++ bindings
    # print(f"Loading GGUF weights directly from: {blob_path}")
    llm = Llama(
        model_path=blob_path,
        n_ctx=4096,        # <- Your custom context frame window size
        n_gpu_layers=-1,   # <- Safe to pass -1 because we cleared VRAM above
        verbose=False,     # <- Silence llama.cpp's tensor/metadata load logging
        embedding=embedding
    )
    return llm

def ask(llm, question, stream=True):
    if not stream:
        output = llm.create_chat_completion(
            messages=[{"role": "user", "content": question}]
        )
        print(output["choices"][0]["message"]["content"])
        return

    for chunk in llm.create_chat_completion(
        messages=[{"role": "user", "content": question}],
        stream=True,
    ):
        delta = chunk["choices"][0]["delta"].get("content", "")
        print(delta, end="", flush=True)
    print()

def repl(llm, stream=True):
    print(f"Model loaded. Streaming is {'ON' if stream else 'OFF'}. Type 'exit' or 'quit' to stop.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue
        print("A: ", end="")
        ask(llm, question, stream=stream)
        print()

def get_embeddings(llm, texts):
    """Runs texts through an embedding-mode Llama model. Returns one vector per input text."""
    result = llm.create_embedding(texts)
    return [item["embedding"] for item in result["data"]]

def make_server_handler(embed_llm, chat_llm):
    class ServerHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # keep request noise out of stdout

        def _send_json(self, status, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._send_json(200, {"status": "ok"})
            else:
                self._send_json(404, {"error": "not found"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError as e:
                self._send_json(400, {"error": str(e)})
                return

            if self.path == "/embeddings":
                self._handle_embeddings(body)
            elif self.path == "/chat":
                self._handle_chat(body)
            else:
                self._send_json(404, {"error": "not found"})

        def _handle_embeddings(self, body):
            try:
                texts = body["texts"]
                if not isinstance(texts, list) or not texts:
                    raise ValueError("'texts' must be a non-empty list of strings")
            except (KeyError, ValueError) as e:
                self._send_json(400, {"error": str(e)})
                return

            embeddings = get_embeddings(embed_llm, texts)
            self._send_json(200, {"embeddings": embeddings})

        def _handle_chat(self, body):
            try:
                question = body["question"]
                if not isinstance(question, str) or not question.strip():
                    raise ValueError("'question' must be a non-empty string")
            except (KeyError, ValueError) as e:
                self._send_json(400, {"error": str(e)})
                return

            output = chat_llm.create_chat_completion(
                messages=[{"role": "user", "content": question}]
            )
            self._send_json(200, {"answer": output["choices"][0]["message"]["content"]})

    return ServerHandler

def serve(embed_llm, chat_llm, host="localhost", port=8000):
    server = ThreadingHTTPServer((host, port), make_server_handler(embed_llm, chat_llm))
    print(f"Server ready at http://{host}:{port} (POST /embeddings, POST /chat, GET /health). Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat REPL / embedding server backed by a locally loaded Ollama GGUF model.")
    parser.add_argument("--no-stream", action="store_true", help="Disable token streaming; print the full answer at once.")
    parser.add_argument("--serve", action="store_true", help="Start the HTTP server (embeddings + chat) instead of the local chat REPL.")
    parser.add_argument("--port", type=int, default=8000, help="Port for the server (default 8000).")
    parser.add_argument("--embed-model", default="nomic-embed-text", help="Ollama embedding model name (default nomic-embed-text).")
    parser.add_argument("--embed-tag", default="latest", help="Tag for the embedding model (default latest).")
    parser.add_argument("--chat-model", default="qwen2.5-coder", help="Ollama chat model name (default qwen2.5-coder).")
    parser.add_argument("--chat-tag", default="7b", help="Tag for the chat model (default 7b).")
    args = parser.parse_args()

    if args.serve:
        embed_llm = load_ollama_model_natively(model_name=args.embed_model, tag=args.embed_tag, embedding=True)
        chat_llm = load_ollama_model_natively(model_name=args.chat_model, tag=args.chat_tag)
        serve(embed_llm, chat_llm, port=args.port)
    else:
        llm = load_ollama_model_natively(model_name="qwen2.5-coder", tag="7b")
        stream = not args.no_stream

        demo_questions = [
            "What is the capital of India?",
            "What is India's independence day?",
        ]
        for question in demo_questions:
            print(f"Q: {question}")
            print("A: ", end="")
            ask(llm, question, stream=stream)
            print()

        repl(llm, stream=stream)