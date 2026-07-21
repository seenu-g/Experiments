# Voice Agent

A local, offline-first voice assistant loop: record → transcribe → ask an LLM →
(optionally run a tool) → speak the answer. Everything runs on your machine —
speech-to-text via Whisper, the LLM via Ollama, and text-to-speech via Piper.

## Flow

```
capture_audio.record_audio()      mic -> audio.wav
        |
audio_to_text.transcribe_audio()  audio.wav -> text   (faster-whisper, "small")
        |
audio_to_text.ask_llm()           text -> LLM response (ollama, llama3:8b)
        |
voice_agent.process_response()    parses a tool call out of the response,
        |                         if any (get_current_time / calculate)
audio_to_text.speak()             text -> response.wav -> played back (piper)
```

The loop in `voice_agent.run_voice_agent()` repeats until you say "exit",
"quit", or "stop".

## Files

| File | Responsibility |
|---|---|
| `voice_agent.py` | Main loop, tool definitions (`get_current_time`, `calculate`), tool-call parsing |
| `capture_audio.py` | Records 5s of mic audio to `audio.wav` |
| `audio_to_text.py` | Whisper transcription, Ollama chat call, Piper text-to-speech playback |

`audio.wav` and `response.wav` are working files regenerated on every turn —
they, along with the Piper voice model, are gitignored (see `.gitignore`).

## Requirements

- **Python deps**: `ollama`, `faster-whisper`, `sounddevice`, `scipy`, `python-dotenv`
- **[Ollama](https://ollama.com)** running locally with a model pulled, e.g.:
  ```
  ollama pull llama3:8b
  ```
- **[Piper](https://github.com/OHF-voice/piper1-gpl)** TTS:
  ```
  pip install piper-tts
  ```
  Piper is located automatically via, in order: the `PIPER_PATH` env var,
  `piper` on your `PATH`, or the default pip user-scripts install location.
- **Piper voice model** — download the ONNX model + its `.json` config into
  this folder (default voice is `en_US-lessac-medium`):
  ```
  curl.exe -L -o en_US-lessac-medium.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
  curl.exe -L -o en_US-lessac-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
  ```

The first run also downloads the `faster-whisper` "small" model automatically
(~460MB) from Hugging Face — this can use the `HF_TOKEN` set in the parent
`llm_examples/.env`.

## Run

```
python voice_agent.py
```

Say something after "Listening..." — e.g. "What time is it?" or "5 multiply
5". Say "stop" to end the session.

## Tools

Tool calls are requested by the LLM as a JSON object (`{"tool": ..., "argument": ...}`)
per the instructions in `tools_description`. Two tools are wired up:

- `get_current_time` — no argument, returns the current local time.
- `calculate` — evaluates a simple arithmetic expression safely (via `ast`,
  not `eval`). Recognizes common aliases (`add`, `subtract`, `multiply`,
  `divide`, ...) and normalizes word operators (`minus`, `times`, `x`,
  `divided by`) so the local LLM's varied phrasing still resolves.

If the model doesn't produce a recognized tool call, the raw LLM response is
spoken as-is, and `[debug] Unrecognized tool call: ...` is printed to the
console to help diagnose model output that didn't match expectations.

## Configuration

- `PIPER_PATH` (optional, in `.env`) — explicit path to `piper`/`piper.exe`
  if it isn't discoverable on `PATH`.
- `HF_TOKEN` (optional, in the parent `llm_examples/.env`) — Hugging Face
  token, picked up automatically via `python-dotenv` for model downloads.
