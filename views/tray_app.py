import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw, ImageFont
import pystray

from models.dictation_state import DictationState

# Icon colors for each state
STATE_COLORS = {
    DictationState.IDLE: "#22c55e",         # green
    DictationState.RECORDING: "#ef4444",     # red
    DictationState.TRANSCRIBING: "#f97316",  # orange
    DictationState.ERROR: "#eab308",         # yellow
}

ICON_SIZE = 64


def _create_microphone_icon(color: str) -> Image.Image:
    """Draw a simple microphone icon with the given color."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Microphone body (rounded rectangle approximation)
    mic_left = 22
    mic_right = 42
    mic_top = 8
    mic_bottom = 38
    draw.rounded_rectangle(
        [mic_left, mic_top, mic_right, mic_bottom],
        radius=10,
        fill=color,
    )

    # Microphone arc (bottom curve)
    arc_padding = 6
    draw.arc(
        [mic_left - arc_padding, mic_bottom - 16, mic_right + arc_padding, mic_bottom + 10],
        start=0, end=180,
        fill=color, width=3,
    )

    # Stand line
    center_x = ICON_SIZE // 2
    draw.line(
        [center_x, mic_bottom + 8, center_x, mic_bottom + 16],
        fill=color, width=3,
    )

    # Base
    draw.line(
        [center_x - 8, mic_bottom + 16, center_x + 8, mic_bottom + 16],
        fill=color, width=3,
    )

    return img


class TrayApp:
    def __init__(self):
        self._icon: Optional[pystray.Icon] = None
        self._icons: dict[DictationState, Image.Image] = {}
        self._current_state = DictationState.IDLE

        # Callbacks (set by main.py)
        self.on_left_click: Optional[Callable] = None
        self.on_settings_click: Optional[Callable] = None
        self.on_quit_click: Optional[Callable] = None

        self._generate_icons()

    def _generate_icons(self):
        for state, color in STATE_COLORS.items():
            self._icons[state] = _create_microphone_icon(color)

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("FlowDictation", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", self._on_settings),
            pystray.MenuItem("Quit", self._on_quit),
        )

    def _on_activate(self, icon, item=None):
        if self.on_left_click:
            self.on_left_click()

    def _on_settings(self, icon=None, item=None):
        if self.on_settings_click:
            self.on_settings_click()

    def _on_quit(self, icon=None, item=None):
        if self.on_quit_click:
            self.on_quit_click()

    def run(self):
        """Run the tray icon (blocking — call from daemon thread)."""
        self._icon = pystray.Icon(
            name="FlowDictation",
            icon=self._icons[DictationState.IDLE],
            title="FlowDictation - Ready",
            menu=self._build_menu(),
        )
        # Left click action
        self._icon.default_action = self._on_activate
        self._icon.run()

    def update_state(self, state: DictationState, error_msg: str = ""):
        """Update the tray icon to reflect current state."""
        self._current_state = state
        if self._icon is None:
            return

        icon_img = self._icons.get(state, self._icons[DictationState.IDLE])
        self._icon.icon = icon_img

        titles = {
            DictationState.IDLE: "FlowDictation - Ready",
            DictationState.RECORDING: "FlowDictation - Recording...",
            DictationState.TRANSCRIBING: "FlowDictation - Transcribing...",
            DictationState.ERROR: f"FlowDictation - Error: {error_msg}",
        }
        self._icon.title = titles.get(state, "FlowDictation")

    def stop(self):
        """Stop the tray icon."""
        if self._icon:
            self._icon.stop()
