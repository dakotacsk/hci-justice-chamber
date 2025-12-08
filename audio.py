import pygame
import pyaudio
import json
import numpy as np
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
        self.listening_enabled = False
        self.current_audio_level = 0.0  # Current audio level (0.0 to 1.0)
        self.audio_level_lock = threading.Lock()  # Thread-safe access to audio level

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
        # Use smaller buffer size for lower latency (1024 samples = ~64ms instead of 256ms)
        buffer_size = 1024
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=buffer_size,
        )

        while self.running:
            try:
                data = stream.read(buffer_size, exception_on_overflow=False)

                # Calculate audio level (RMS) for visual feedback
                audio_data = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_data**2))
                # Normalize to 0-1 range (int16 max is 32768)
                normalized_level = min(1.0, rms / 32768.0)

                # Update audio level thread-safely
                with self.audio_level_lock:
                    self.current_audio_level = normalized_level

                # Don't block if queue is full - drop old audio to prevent lag
                if self.listening_enabled:
                    if self.audio_queue.qsize() < 3:
                        self.audio_queue.put(data)
                    else:
                        try:
                            self.audio_queue.get_nowait()
                        except:
                            pass
                        self.audio_queue.put(data)
            except Exception as e:
                # Continue on errors to prevent crashes
                continue

        stream.stop_stream()
        stream.close()
        p.terminate()

    def _recognize_loop(self):
        """Process audio in background"""
        while self.running:
            # Process multiple chunks per iteration to catch up faster
            chunks_processed = 0
            max_chunks_per_iteration = 5

            while chunks_processed < max_chunks_per_iteration:
                try:
                    # Get audio data (non-blocking if queue is empty)
                    data = self.audio_queue.get_nowait()
                except:
                    # Queue is empty, break to sleep
                    break

                # Process audio chunk
                if self.recognizer.AcceptWaveform(data):
                    # Final result (complete phrase)
                    result = json.loads(self.recognizer.Result())
                    if result["text"]:
                        self.result_queue.put(result["text"])
                else:
                    # Check for partial results (user still speaking) - helps keep recognizer responsive
                    try:
                        partial = json.loads(self.recognizer.PartialResult())
                        # Partial results help the recognizer stay responsive but we don't need to process them
                    except:
                        pass

                chunks_processed += 1

            # Sleep briefly if we processed all chunks or queue was empty
            if chunks_processed == 0:
                time.sleep(0.01)  # Avoid busy-waiting when queue is empty
            elif chunks_processed >= max_chunks_per_iteration:
                # Processed max chunks, continue immediately to process more
                continue

    def get_latest_text(self):
        """Non-blocking check for new speech (call in game loop)"""
        if not self.result_queue.empty():
            return self.result_queue.get()
        return None

    def get_audio_level(self):
        """Get current audio level (0.0 to 1.0) for visual feedback"""
        with self.audio_level_lock:
            return self.current_audio_level


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
