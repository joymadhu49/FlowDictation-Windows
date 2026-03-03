import json
import os
import threading
from typing import Optional
from models.dictation_state import HotkeyOption, CustomHotkeyConfig


def _get_config_dir() -> str:
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    config_dir = os.path.join(appdata, "FlowDictation")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def _get_config_path() -> str:
    return os.path.join(_get_config_dir(), "settings.json")


_DEFAULTS = {
    "api_key": "",
    "selected_hotkey": HotkeyOption.RIGHT_ALT.value,
    "custom_hotkey": None,
    "sound_enabled": True,
    "sound_volume": 0.4,
    "auto_insert_text": True,
}


class Config:
    def __init__(self):
        self._lock = threading.Lock()
        self._data: dict = {}
        self._load()

    def _load(self):
        with self._lock:
            path = _get_config_path()
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self._data = json.load(f)
                except (json.JSONDecodeError, OSError):
                    self._data = {}
            else:
                self._data = {}

    def _save(self):
        with self._lock:
            path = _get_config_path()
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2)
            except OSError:
                pass

    def _get(self, key: str, default=None):
        with self._lock:
            return self._data.get(key, default if default is not None else _DEFAULTS.get(key))

    def _set(self, key: str, value):
        with self._lock:
            self._data[key] = value
        self._save()

    # --- Properties ---

    @property
    def api_key(self) -> str:
        return self._get("api_key", "")

    @api_key.setter
    def api_key(self, value: str):
        self._set("api_key", value)

    @property
    def selected_hotkey(self) -> HotkeyOption:
        raw = self._get("selected_hotkey", HotkeyOption.RIGHT_ALT.value)
        try:
            return HotkeyOption(raw)
        except ValueError:
            return HotkeyOption.RIGHT_ALT

    @selected_hotkey.setter
    def selected_hotkey(self, value: HotkeyOption):
        self._set("selected_hotkey", value.value)

    @property
    def custom_hotkey(self) -> Optional[CustomHotkeyConfig]:
        raw = self._get("custom_hotkey")
        if raw and isinstance(raw, dict):
            return CustomHotkeyConfig.from_dict(raw)
        return None

    @custom_hotkey.setter
    def custom_hotkey(self, value: Optional[CustomHotkeyConfig]):
        self._set("custom_hotkey", value.to_dict() if value else None)

    @property
    def sound_enabled(self) -> bool:
        return self._get("sound_enabled", True)

    @sound_enabled.setter
    def sound_enabled(self, value: bool):
        self._set("sound_enabled", value)

    @property
    def sound_volume(self) -> float:
        return self._get("sound_volume", 0.4)

    @sound_volume.setter
    def sound_volume(self, value: float):
        self._set("sound_volume", max(0.0, min(1.0, value)))

    @property
    def auto_insert_text(self) -> bool:
        return self._get("auto_insert_text", True)

    @auto_insert_text.setter
    def auto_insert_text(self, value: bool):
        self._set("auto_insert_text", value)
