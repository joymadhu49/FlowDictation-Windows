import threading
from typing import Callable, Optional
import keyboard
from models.dictation_state import HotkeyOption, CustomHotkeyConfig

# Scan code for Right Alt on Windows
RIGHT_ALT_SCAN_CODE = 3640
RIGHT_SHIFT_SCAN_CODE = 54


class GlobalHotkeyManager:
    def __init__(self):
        self._hotkey_option: HotkeyOption = HotkeyOption.RIGHT_ALT
        self._custom_config: Optional[CustomHotkeyConfig] = None
        self._on_hotkey_down: Optional[Callable] = None
        self._on_hotkey_up: Optional[Callable] = None
        self._is_hotkey_down = False
        self._hook = None
        self._lock = threading.Lock()

    @property
    def hotkey_option(self) -> HotkeyOption:
        return self._hotkey_option

    @hotkey_option.setter
    def hotkey_option(self, value: HotkeyOption):
        was_running = self._hook is not None
        if was_running:
            self.stop()
        self._hotkey_option = value
        if was_running:
            self.start()

    @property
    def custom_config(self) -> Optional[CustomHotkeyConfig]:
        return self._custom_config

    @custom_config.setter
    def custom_config(self, value: Optional[CustomHotkeyConfig]):
        self._custom_config = value

    def set_callbacks(self, on_down: Callable, on_up: Callable):
        self._on_hotkey_down = on_down
        self._on_hotkey_up = on_up

    def start(self):
        """Start listening for global hotkey events."""
        if self._hook is not None:
            return
        self._is_hotkey_down = False
        self._hook = keyboard.hook(self._on_key_event, suppress=False)

    def stop(self):
        """Stop listening for global hotkey events."""
        if self._hook is not None:
            keyboard.unhook(self._hook)
            self._hook = None
        self._is_hotkey_down = False

    def _on_key_event(self, event: keyboard.KeyboardEvent):
        with self._lock:
            matched = self._match_event(event)
            if not matched:
                return

            if event.event_type == keyboard.KEY_DOWN:
                if not self._is_hotkey_down:
                    self._is_hotkey_down = True
                    if self._on_hotkey_down:
                        self._on_hotkey_down()
            elif event.event_type == keyboard.KEY_UP:
                if self._is_hotkey_down:
                    self._is_hotkey_down = False
                    if self._on_hotkey_up:
                        self._on_hotkey_up()

    def _match_event(self, event: keyboard.KeyboardEvent) -> bool:
        """Check if this keyboard event matches the configured hotkey."""
        name = (event.name or "").lower()
        scan = event.scan_code

        if self._hotkey_option == HotkeyOption.ALT:
            return name == "alt" or scan in (56, RIGHT_ALT_SCAN_CODE)

        if self._hotkey_option == HotkeyOption.RIGHT_ALT:
            # Right Alt has scan code 3640 on Windows
            return scan == RIGHT_ALT_SCAN_CODE

        if self._hotkey_option == HotkeyOption.CONTROL:
            return name in ("ctrl", "control", "left ctrl", "right ctrl")

        if self._hotkey_option == HotkeyOption.RIGHT_SHIFT:
            return name == "right shift" or scan == RIGHT_SHIFT_SCAN_CODE

        if self._hotkey_option == HotkeyOption.CUSTOM:
            if self._custom_config:
                if self._custom_config.scan_code is not None:
                    return scan == self._custom_config.scan_code
                return name == self._custom_config.key_name.lower()

        return False
