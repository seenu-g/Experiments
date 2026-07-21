import os

import sounddevice as sd
from scipy.io.wavfile import write

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# sampling rate of 16,000 Hz to  work well with speech recognition models.
#  listens for five seconds at a time
def record_audio(filename=None, duration=5):
    filename = filename or os.path.join(BASE_DIR, "audio.wav")
    sample_rate = 16000

    print("Say something. Listening...")

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(filename, sample_rate, audio)

    print("Recording complete.")