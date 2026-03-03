import os
import wave
import tempfile
import uuid
import threading
import numpy as np
import sounddevice as sd


SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = np.int16
BLOCKSIZE = 1024


class AudioRecorder:
    def __init__(self):
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._recording = False
        self._lock = threading.Lock()
        self._temp_path: str | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> bool:
        """Start recording audio. Returns True on success."""
        with self._lock:
            if self._recording:
                return False
            self._frames = []
            self._recording = True

        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=BLOCKSIZE,
                callback=self._audio_callback,
            )
            self._stream.start()
            return True
        except Exception as e:
            self._recording = False
            raise RuntimeError(f"Failed to start recording: {e}")

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        if self._recording:
            self._frames.append(indata.copy())

    def stop(self) -> str | None:
        """Stop recording and return path to the WAV file, or None if nothing recorded."""
        with self._lock:
            if not self._recording:
                return None
            self._recording = False

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if not self._frames:
            return None

        audio_data = np.concatenate(self._frames, axis=0)
        self._frames = []

        temp_dir = tempfile.gettempdir()
        self._temp_path = os.path.join(temp_dir, f"flowdictation_{uuid.uuid4().hex}.wav")

        try:
            with wave.open(self._temp_path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_data.tobytes())
            return self._temp_path
        except Exception as e:
            self._temp_path = None
            raise RuntimeError(f"Failed to save recording: {e}")

    def cleanup(self):
        """Remove the temporary WAV file."""
        if self._temp_path and os.path.exists(self._temp_path):
            try:
                os.remove(self._temp_path)
            except OSError:
                pass
            self._temp_path = None

    def cancel(self):
        """Cancel an in-progress recording without saving."""
        with self._lock:
            self._recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self._frames = []
