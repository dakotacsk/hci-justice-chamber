import pygame
import pyaudio
import json
from vosk import Model, KaldiRecognizer
import threading
from queue import Queue
import time


class SpeechRecognizer:
    def __init__(self, model_path="vosk-model-small-en-us-0.15"):
        """Initialize Vosk model in background thread"""
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.audio_queue = Queue()
        self.result_queue = Queue()
        self.running = False

    def start(self):
        """Start recognition in separate thread"""
        self.running = True
        threading.Thread(target=self._recognize_loop, daemon=True).start()
        threading.Thread(target=self._audio_capture, daemon=True).start()

    def stop(self):
        self.running = False

    def _audio_capture(self):
        """Capture audio without blocking game"""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096,
        )

        while self.running:
            data = stream.read(4096, exception_on_overflow=False)
            self.audio_queue.put(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

    def _recognize_loop(self):
        """Process audio in background"""
        while self.running:
            data = self.audio_queue.get()
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if result["text"]:
                    self.result_queue.put(result["text"])

    def get_latest_text(self):
        """Non-blocking check for new speech (call in game loop)"""
        if not self.result_queue.empty():
            return self.result_queue.get()
        return None


# Pygame integration example
def main():
    # Initialize speech recognizer
    speech = SpeechRecognizer()
    speech.start()

    current_text = "Say something..."
    running = True

    start_time = time.perf_counter()

    # Run for 30 seconds
    while time.perf_counter() - start_time < 30:
        # Non-blocking check for speech (THIS IS KEY FOR PYGAME)
        new_speech = speech.get_latest_text()
        if new_speech:
            current_text = f"Heard: {new_speech}"
            print(f"Voice command: {new_speech}")

    speech.stop()


if __name__ == "__main__":
    main()
