from enum import Enum
from dataclasses import dataclass
from typing import Optional


class DictationState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    ERROR = "error"


class HotkeyOption(Enum):
    ALT = "alt"
    RIGHT_ALT = "right alt"
    CONTROL = "control"
    RIGHT_SHIFT = "right shift"
    CUSTOM = "custom"

    @property
    def display_name(self) -> str:
        names = {
            HotkeyOption.ALT: "Alt (Either)",
            HotkeyOption.RIGHT_ALT: "Right Alt",
            HotkeyOption.CONTROL: "Control",
            HotkeyOption.RIGHT_SHIFT: "Right Shift",
            HotkeyOption.CUSTOM: "Custom",
        }
        return names[self]

    @property
    def is_modifier(self) -> bool:
        return self in (
            HotkeyOption.ALT,
            HotkeyOption.RIGHT_ALT,
            HotkeyOption.CONTROL,
            HotkeyOption.RIGHT_SHIFT,
        )


@dataclass
class CustomHotkeyConfig:
    key_name: str  # keyboard library key name
    scan_code: Optional[int] = None  # scan code for disambiguation
    display_name: str = ""  # human-readable label

    def to_dict(self) -> dict:
        return {
            "key_name": self.key_name,
            "scan_code": self.scan_code,
            "display_name": self.display_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CustomHotkeyConfig":
        return cls(
            key_name=data.get("key_name", ""),
            scan_code=data.get("scan_code"),
            display_name=data.get("display_name", ""),
        )
