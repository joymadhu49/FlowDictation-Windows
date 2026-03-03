import time
import threading
from typing import Callable, Optional

from models.dictation_state import DictationState, HotkeyOption, CustomHotkeyConfig
from config import Config
from services.audio_recorder import AudioRecorder
from services.groq_api_client import GroqAPIClient, GroqAPIError
from services.global_hotkey_manager import GlobalHotkeyManager
from services.text_inserter import TextInserter
from services.sound_feedback import SoundFeedback

MIN_RECORDING_DURATION = 0.3  # seconds
ERROR_RESET_DELAY = 5.0  # seconds


class DictationManager:
    def __init__(self, config: Config):
        self.config = config

        # Services
        self.recorder = AudioRecorder()
        self.api_client = GroqAPIClient(config.api_key)
        self.hotkey_manager = GlobalHotkeyManager()
        self.text_inserter = TextInserter()
        self.sound = SoundFeedback()

        # State
        self._state = DictationState.IDLE
        self._is_enabled = True
        self._last_transcription = ""
        self._recording_duration = 0.0
        self._recording_start_time: Optional[float] = None
        self._duration_timer: Optional[threading.Timer] = None
        self._error_message = ""

        # Callbacks (set by UI layer)
        self.on_state_changed: Optional[Callable[[DictationState, str], None]] = None
        self.on_transcription_changed: Optional[Callable[[str], None]] = None
        self.on_duration_changed: Optional[Callable[[float], None]] = None

        # Apply config
        self._apply_config()

        # Wire hotkey callbacks
        self.hotkey_manager.set_callbacks(
            on_down=self._on_hotkey_down,
            on_up=self._on_hotkey_up,
        )

    def _apply_config(self):
        self.api_client.api_key = self.config.api_key
        self.hotkey_manager.hotkey_option = self.config.selected_hotkey
        self.hotkey_manager.custom_config = self.config.custom_hotkey
        self.sound.volume = self.config.sound_volume

    def reload_config(self):
        """Re-apply settings from config (call after settings change)."""
        self._apply_config()

    @property
    def state(self) -> DictationState:
        return self._state

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled

    @is_enabled.setter
    def is_enabled(self, value: bool):
        self._is_enabled = value
        if not value and self._state == DictationState.RECORDING:
            self._cancel_recording()

    @property
    def last_transcription(self) -> str:
        return self._last_transcription

    @property
    def recording_duration(self) -> float:
        return self._recording_duration

    @property
    def error_message(self) -> str:
        return self._error_message

    def _set_state(self, state: DictationState, error_msg: str = ""):
        self._state = state
        self._error_message = error_msg
        if self.on_state_changed:
            self.on_state_changed(state, error_msg)

    def start(self):
        """Start the hotkey listener."""
        self.hotkey_manager.start()

    def stop(self):
        """Stop the hotkey listener and clean up."""
        self.hotkey_manager.stop()
        if self._state == DictationState.RECORDING:
            self._cancel_recording()

    def _on_hotkey_down(self):
        if not self._is_enabled:
            return
        if self._state != DictationState.IDLE:
            return
        if not self.config.api_key:
            self._set_error("No API key. Set your Groq API key in Settings.")
            return

        try:
            self.recorder.start()
        except RuntimeError as e:
            self._set_error(str(e))
            return

        self._recording_start_time = time.time()
        self._recording_duration = 0.0
        self._set_state(DictationState.RECORDING)

        if self.config.sound_enabled:
            self.sound.play_start()

        self._start_duration_timer()

    def _on_hotkey_up(self):
        if self._state != DictationState.RECORDING:
            return

        self._stop_duration_timer()
        elapsed = time.time() - (self._recording_start_time or time.time())
        self._recording_duration = elapsed

        if elapsed < MIN_RECORDING_DURATION:
            self._cancel_recording()
            return

        # Stop recording and get file path
        audio_path = self.recorder.stop()
        if not audio_path:
            self._cancel_recording()
            return

        if self.config.sound_enabled:
            self.sound.play_stop()

        self._set_state(DictationState.TRANSCRIBING)

        # Transcribe on background thread
        threading.Thread(
            target=self._transcribe, args=(audio_path,), daemon=True
        ).start()

    def _transcribe(self, audio_path: str):
        try:
            text = self.api_client.transcribe(audio_path)
            self._last_transcription = text

            if self.on_transcription_changed:
                self.on_transcription_changed(text)

            # Insert or copy text
            if self.config.auto_insert_text:
                self.text_inserter.insert(text)
            else:
                self.text_inserter.copy_only(text)

            if self.config.sound_enabled:
                self.sound.play_success()

            self._set_state(DictationState.IDLE)

        except GroqAPIError as e:
            self._set_error(str(e))
        except Exception as e:
            self._set_error(f"Transcription failed: {e}")
        finally:
            self.recorder.cleanup()

    def _cancel_recording(self):
        self._stop_duration_timer()
        self.recorder.cancel()
        self.recorder.cleanup()
        self._set_state(DictationState.IDLE)

    def _set_error(self, message: str):
        if self.config.sound_enabled:
            self.sound.play_error()
        self._set_state(DictationState.ERROR, message)
        # Auto-reset after delay
        threading.Timer(ERROR_RESET_DELAY, self._reset_error).start()

    def _reset_error(self):
        if self._state == DictationState.ERROR:
            self._set_state(DictationState.IDLE)

    def _start_duration_timer(self):
        def tick():
            if self._state == DictationState.RECORDING and self._recording_start_time:
                self._recording_duration = time.time() - self._recording_start_time
                if self.on_duration_changed:
                    self.on_duration_changed(self._recording_duration)
                self._duration_timer = threading.Timer(0.1, tick)
                self._duration_timer.daemon = True
                self._duration_timer.start()

        self._duration_timer = threading.Timer(0.1, tick)
        self._duration_timer.daemon = True
        self._duration_timer.start()

    def _stop_duration_timer(self):
        if self._duration_timer:
            self._duration_timer.cancel()
            self._duration_timer = None
