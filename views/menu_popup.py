import customtkinter as ctk
from typing import Callable, Optional

from models.dictation_state import DictationState

# State display config
STATE_DISPLAY = {
    DictationState.IDLE: ("Ready", "#22c55e"),
    DictationState.RECORDING: ("Recording", "#ef4444"),
    DictationState.TRANSCRIBING: ("Transcribing...", "#f97316"),
    DictationState.ERROR: ("Error", "#eab308"),
}

POPUP_WIDTH = 320
POPUP_HEIGHT = 380


class MenuPopup(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)

        self.title("")
        self.overrideredirect(True)  # borderless
        self.attributes("-topmost", True)
        self.configure(fg_color="#1e1e2e")
        self.geometry(f"{POPUP_WIDTH}x{POPUP_HEIGHT}")

        # Callbacks
        self.on_copy_click: Optional[Callable] = None
        self.on_toggle_enabled: Optional[Callable[[bool], None]] = None
        self.on_toggle_sound: Optional[Callable[[bool], None]] = None
        self.on_settings_click: Optional[Callable] = None
        self.on_quit_click: Optional[Callable] = None

        self._build_ui()
        self.withdraw()  # start hidden

        # Hide on focus loss
        self.bind("<FocusOut>", self._on_focus_out)

    def _build_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(12, 4))

        self._title_label = ctk.CTkLabel(
            header_frame, text="FlowDictation",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#cdd6f4",
        )
        self._title_label.pack(side="left")

        self._status_badge = ctk.CTkLabel(
            header_frame, text="Ready",
            font=ctk.CTkFont(size=12),
            text_color="#1e1e2e",
            fg_color="#22c55e",
            corner_radius=8,
            width=90, height=24,
        )
        self._status_badge.pack(side="right")

        # Separator
        ctk.CTkFrame(self, height=1, fg_color="#313244").pack(fill="x", padx=16, pady=8)

        # Recording info
        self._recording_frame = ctk.CTkFrame(self, fg_color="#313244", corner_radius=8)
        self._recording_frame.pack(fill="x", padx=16, pady=4)

        self._recording_label = ctk.CTkLabel(
            self._recording_frame, text="Hold hotkey to record",
            font=ctk.CTkFont(size=13),
            text_color="#a6adc8",
        )
        self._recording_label.pack(padx=12, pady=8)

        # Last transcription
        self._transcription_frame = ctk.CTkFrame(self, fg_color="#313244", corner_radius=8)
        self._transcription_frame.pack(fill="x", padx=16, pady=4)

        trans_header = ctk.CTkFrame(self._transcription_frame, fg_color="transparent")
        trans_header.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            trans_header, text="Last Transcription",
            font=ctk.CTkFont(size=11),
            text_color="#6c7086",
        ).pack(side="left")

        self._copy_btn = ctk.CTkButton(
            trans_header, text="Copy", width=50, height=24,
            font=ctk.CTkFont(size=11),
            fg_color="#45475a", hover_color="#585b70",
            command=self._on_copy,
        )
        self._copy_btn.pack(side="right")

        self._transcription_text = ctk.CTkLabel(
            self._transcription_frame,
            text="No transcription yet",
            font=ctk.CTkFont(size=13),
            text_color="#cdd6f4",
            wraplength=POPUP_WIDTH - 56,
            justify="left",
            anchor="w",
        )
        self._transcription_text.pack(fill="x", padx=12, pady=(0, 8))

        # Separator
        ctk.CTkFrame(self, height=1, fg_color="#313244").pack(fill="x", padx=16, pady=8)

        # Quick toggles
        toggles_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=16, pady=2)

        self._enabled_var = ctk.BooleanVar(value=True)
        self._enabled_switch = ctk.CTkSwitch(
            toggles_frame, text="Enabled",
            font=ctk.CTkFont(size=13),
            text_color="#cdd6f4",
            variable=self._enabled_var,
            command=self._on_enabled_toggle,
        )
        self._enabled_switch.pack(side="left")

        self._sound_var = ctk.BooleanVar(value=True)
        self._sound_switch = ctk.CTkSwitch(
            toggles_frame, text="Sound",
            font=ctk.CTkFont(size=13),
            text_color="#cdd6f4",
            variable=self._sound_var,
            command=self._on_sound_toggle,
        )
        self._sound_switch.pack(side="right")

        # Bottom buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(8, 12))

        ctk.CTkButton(
            btn_frame, text="Settings",
            font=ctk.CTkFont(size=13),
            fg_color="#45475a", hover_color="#585b70",
            height=32,
            command=self._on_settings,
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="Quit",
            font=ctk.CTkFont(size=13),
            fg_color="#45475a", hover_color="#f38ba8",
            height=32,
            command=self._on_quit,
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

    def show_near_taskbar(self):
        """Position popup above the taskbar and show it."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = screen_w - POPUP_WIDTH - 16
        y = screen_h - POPUP_HEIGHT - 60  # above taskbar
        self.geometry(f"{POPUP_WIDTH}x{POPUP_HEIGHT}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide(self):
        self.withdraw()

    def _on_focus_out(self, event=None):
        # Only hide if focus went to a widget outside this window
        try:
            focused = self.focus_get()
            if focused and str(focused).startswith(str(self)):
                return
        except Exception:
            pass
        self.after(100, self.hide)

    def update_state(self, state: DictationState, error_msg: str = ""):
        label, color = STATE_DISPLAY.get(state, ("Ready", "#22c55e"))
        if state == DictationState.ERROR and error_msg:
            label = "Error"
        self._status_badge.configure(text=label, fg_color=color)

        if state == DictationState.RECORDING:
            self._recording_label.configure(text="Recording...", text_color="#ef4444")
        elif state == DictationState.TRANSCRIBING:
            self._recording_label.configure(text="Transcribing...", text_color="#f97316")
        elif state == DictationState.ERROR:
            self._recording_label.configure(
                text=error_msg or "An error occurred", text_color="#eab308"
            )
        else:
            self._recording_label.configure(
                text="Hold hotkey to record", text_color="#a6adc8"
            )

    def update_duration(self, duration: float):
        if duration > 0:
            self._recording_label.configure(
                text=f"Recording... {duration:.1f}s", text_color="#ef4444"
            )

    def update_transcription(self, text: str):
        display = text if text else "No transcription yet"
        # Truncate for display
        if len(display) > 200:
            display = display[:200] + "..."
        self._transcription_text.configure(text=display)

    def set_enabled(self, enabled: bool):
        self._enabled_var.set(enabled)

    def set_sound_enabled(self, enabled: bool):
        self._sound_var.set(enabled)

    def _on_copy(self):
        if self.on_copy_click:
            self.on_copy_click()

    def _on_enabled_toggle(self):
        if self.on_toggle_enabled:
            self.on_toggle_enabled(self._enabled_var.get())

    def _on_sound_toggle(self):
        if self.on_toggle_sound:
            self.on_toggle_sound(self._sound_var.get())

    def _on_settings(self):
        if self.on_settings_click:
            self.on_settings_click()
        self.hide()

    def _on_quit(self):
        if self.on_quit_click:
            self.on_quit_click()
