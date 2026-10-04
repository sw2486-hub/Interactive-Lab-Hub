#!/usr/bin/env python3
"""Wizard of Oz voice-controlled vacuum prototype for Lab 3."""

import argparse
import time

import numpy as np
import sherpa_onnx
import sounddevice as sd
from faster_whisper import WhisperModel

from echo_bot import DEFAULT_VAD, DEFAULT_VOICE, SAMPLE_RATE, Speaker


PROMPTS = {
    "room": "Which room should I clean?",
    "clarify": "Do you mean the area around the table in the living room?",
    "mode": "Would you like standard or quiet mode?",
    "confirm": "Should I start cleaning the living room in quiet mode?",
    "start": "Starting now. I am cleaning the living room.",
    "progress": "I am still cleaning the living room.",
    "pause": "Cleaning paused.",
    "resume": "Resuming cleaning.",
    "stop": "Cleaning stopped.",
    "repeat": "Sorry, I did not understand. Could you say that again?",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="tiny.en")
    parser.add_argument("--min-silence", type=float, default=1.0)
    args = parser.parse_args()

    for path in (DEFAULT_VAD, DEFAULT_VOICE):
        if not path.is_file():
            parser.error(f"Missing {path}; run ./setup.sh first")

    print("Loading models...", flush=True)
    recognizer = WhisperModel(
        args.model,
        device="cpu",
        compute_type="int8",
    )
    speaker = Speaker(DEFAULT_VOICE)

    config = sherpa_onnx.VadModelConfig()
    config.silero_vad.model = str(DEFAULT_VAD)
    config.silero_vad.min_silence_duration = args.min_silence
    config.sample_rate = SAMPLE_RATE

    vad = sherpa_onnx.VoiceActivityDetector(
        config,
        buffer_size_in_seconds=30,
    )
    window = config.silero_vad.window_size
    buffer = np.empty(0, dtype=np.float32)
    status = "READY"

    print("Controller: choose a response after each spoken turn. q quits.")
    speaker.say("I am ready. Tell me what to clean.")

    with sd.InputStream(
        channels=1,
        dtype="float32",
        samplerate=SAMPLE_RATE,
    ) as stream:
        while True:
            print(f"SYSTEM: Listening... ({status})", flush=True)

            while vad.empty():
                chunk, _ = stream.read(int(0.1 * SAMPLE_RATE))
                buffer = np.concatenate([buffer, chunk.reshape(-1)])

                while len(buffer) >= window:
                    vad.accept_waveform(buffer[:window])
                    buffer = buffer[window:]

            utterance = np.array(vad.front.samples, dtype=np.float32)
            vad.pop()

            print("SYSTEM: Thinking...", flush=True)
            started = time.perf_counter()

            segments, _ = recognizer.transcribe(
                utterance,
                beam_size=1,
            )
            heard = " ".join(
                segment.text.strip() for segment in segments
            )

            print(f"CONTROLLER heard: {heard or '[no words recognized]'}")
            print(
                "CONTROLLER choices: "
                + ", ".join(PROMPTS)
                + ", custom, q"
            )
            choice = input("CONTROLLER choose: ").strip().lower()

            if choice == "q":
                break

            if choice == "custom":
                reply = input("CONTROLLER exact reply: ").strip()
            else:
                reply = PROMPTS.get(choice)

            if not reply:
                print("Unknown choice or empty reply. Try again next turn.")
                continue

            if choice in ("start", "resume"):
                status = "CLEANING (simulated)"
            elif choice == "pause":
                status = "PAUSED"
            elif choice == "stop":
                status = "STOPPED"

            print(
                f"SYSTEM: Speaking... "
                f"(ASR {time.perf_counter() - started:.2f}s)"
            )
            stream.stop()
            speaker.say(reply)
            stream.start()
            print(f"SYSTEM said: {reply}\n", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
