import argparse
import os
import json
import urllib.request
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

def load_ollama_model_natively(model_name="llama3", tag="latest"):
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
        n_ctx=4096,      # <- Your custom context frame window size
        n_gpu_layers=-1, # <- Safe to pass -1 because we cleared VRAM above
        verbose=False    # <- Silence llama.cpp's tensor/metadata load logging
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat REPL backed by a locally loaded Ollama GGUF model.")
    parser.add_argument("--no-stream", action="store_true", help="Disable token streaming; print the full answer at once.")
    args = parser.parse_args()

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