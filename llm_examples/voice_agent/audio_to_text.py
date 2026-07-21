import os
import shutil
import subprocess

import ollama
import sounddevice as sd
from faster_whisper import WhisperModel
from scipy.io.wavfile import read

whisper_model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PIPER_MODEL = os.path.join(BASE_DIR, "en_US-lessac-medium.onnx")
PIPER_EXE = (
    os.getenv("PIPER_PATH")
    or shutil.which("piper")
    or os.path.join(os.getenv("APPDATA", ""), "Python", "Python314", "Scripts", "piper.exe")
)


def transcribe_audio(filename=None):
    filename = filename or os.path.join(BASE_DIR, "audio.wav")
    segments, info = whisper_model.transcribe(
        filename,
        initial_prompt="Numbers and simple math: add, subtract, multiply, divide, plus, minus, times, divided by.",
    )

    text = " ".join(
        segment.text for segment in segments
    )

    return text.strip()


def ask_llm(user_text, tools_description):
    prompt = f"""
You are a helpful Voice AI Agent.

{tools_description}

User request:
{user_text}
"""

    response = ollama.chat(
        model="llama3:8b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


def speak(text):
    output_path = os.path.join(BASE_DIR, "response.wav")

    command = [
        PIPER_EXE,
        "--model",
        PIPER_MODEL,
        "--output_file",
        output_path
    ]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        text=True
    )

    process.communicate(text)

    rate, audio = read(output_path)
    sd.play(audio, rate)
    sd.wait()
