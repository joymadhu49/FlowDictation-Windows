import threading
import customtkinter as ctk
from typing import Callable, Optional

from models.dictation_state import HotkeyOption, CustomHotkeyConfig

WINDOW_WIDTH = 500
WINDOW_HEIGHT = 480


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)

        self.title("FlowDictation - Settings")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color="#1e1e2e")

        # Callbacks
        self.on_save: Optional[Callable[[dict], None]] = None
        self.on_test_connection: Optional[Callable[[], tuple[bool, str]]] = None

        # Current values (set before showing)
        self._api_key = ""
        self._selected_hotkey = HotkeyOption.RIGHT_ALT
        self._custom_hotkey: Optional[CustomHotkeyConfig] = None
        self._auto_insert = True
        self._sound_enabled = True
        self._sound_volume = 0.4

        self._recording_custom_hotkey = False

        self._build_ui()
        self.withdraw()
        self.protocol("WM_DELETE_WINDOW", self.hide)

    def _build_ui(self):
        self._tabview = ctk.CTkTabview(
            self, fg_color="#1e1e2e",
            segmented_button_fg_color="#313244",
            segmented_button_selected_color="#45475a",
            segmented_button_unselected_color="#313244",
        )
        self._tabview.pack(fill="both", expand=True, padx=16, pady=16)

        self._build_general_tab()
        self._build_api_tab()
        self._build_about_tab()

    # ---- General Tab ----

    def _build_general_tab(self):
        tab = self._tabview.add("General")

        # Hotkey selection
        ctk.CTkLabel(
            tab, text="Dictation Hotkey",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=8, pady=(8, 4))

        self._hotkey_var = ctk.StringVar(value=self._selected_hotkey.value)
        hotkey_frame = ctk.CTkFrame(tab, fg_color="transparent")
        hotkey_frame.pack(fill="x", padx=8, pady=4)

        self._hotkey_menu = ctk.CTkOptionMenu(
            hotkey_frame,
            values=[opt.display_name for opt in HotkeyOption],
            command=self._on_hotkey_changed,
            fg_color="#313244",
            button_color="#45475a",
            button_hover_color="#585b70",
            dropdown_fg_color="#313244",
            width=200,
        )
        self._hotkey_menu.pack(side="left")

        # Custom hotkey recorder
        self._custom_frame = ctk.CTkFrame(tab, fg_color="#313244", corner_radius=8)
        self._custom_frame.pack(fill="x", padx=8, pady=4)

        self._custom_label = ctk.CTkLabel(
            self._custom_frame,
            text="Custom: None",
            font=ctk.CTkFont(size=13),
            text_color="#a6adc8",
        )
        self._custom_label.pack(side="left", padx=12, pady=8)

        self._record_btn = ctk.CTkButton(
            self._custom_frame, text="Record Key",
            width=100, height=28,
            font=ctk.CTkFont(size=12),
            fg_color="#45475a", hover_color="#585b70",
            command=self._start_recording_hotkey,
        )
        self._record_btn.pack(side="right", padx=12, pady=8)

        self._custom_frame.pack_forget()  # hidden by default

        # Separator
        ctk.CTkFrame(tab, height=1, fg_color="#313244").pack(fill="x", padx=8, pady=12)

        # Auto-insert toggle
        self._auto_insert_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            tab, text="Auto-insert text at cursor",
            font=ctk.CTkFont(size=13),
            text_color="#cdd6f4",
            variable=self._auto_insert_var,
        ).pack(anchor="w", padx=8, pady=4)

        ctk.CTkLabel(
            tab,
            text="When disabled, text is only copied to clipboard",
            font=ctk.CTkFont(size=11),
            text_color="#6c7086",
        ).pack(anchor="w", padx=28, pady=(0, 8))

        # Sound toggle
        self._sound_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            tab, text="Sound feedback",
            font=ctk.CTkFont(size=13),
            text_color="#cdd6f4",
            variable=self._sound_var,
        ).pack(anchor="w", padx=8, pady=4)

        # Volume slider
        vol_frame = ctk.CTkFrame(tab, fg_color="transparent")
        vol_frame.pack(fill="x", padx=28, pady=4)

        ctk.CTkLabel(
            vol_frame, text="Volume:",
            font=ctk.CTkFont(size=12),
            text_color="#a6adc8",
        ).pack(side="left")

        self._volume_slider = ctk.CTkSlider(
            vol_frame, from_=0.05, to=1.0,
            number_of_steps=19,
            width=200,
        )
        self._volume_slider.pack(side="left", padx=8)
        self._volume_slider.set(0.4)

        self._volume_label = ctk.CTkLabel(
            vol_frame, text="40%",
            font=ctk.CTkFont(size=12),
            text_color="#a6adc8",
            width=40,
        )
        self._volume_label.pack(side="left")
        self._volume_slider.configure(command=self._on_volume_changed)

        # Enable/Disable
        ctk.CTkFrame(tab, height=1, fg_color="#313244").pack(fill="x", padx=8, pady=12)

        self._enabled_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            tab, text="Enable FlowDictation",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#cdd6f4",
            variable=self._enabled_var,
        ).pack(anchor="w", padx=8, pady=4)

        # Save button
        ctk.CTkButton(
            tab, text="Save Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#22c55e", hover_color="#16a34a",
            text_color="#1e1e2e",
            height=36,
            command=self._save,
        ).pack(fill="x", padx=8, pady=(12, 4))

    # ---- API Tab ----

    def _build_api_tab(self):
        tab = self._tabview.add("API")

        ctk.CTkLabel(
            tab, text="Groq API Key",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cdd6f4",
        ).pack(anchor="w", padx=8, pady=(8, 4))

        key_frame = ctk.CTkFrame(tab, fg_color="transparent")
        key_frame.pack(fill="x", padx=8, pady=4)

        self._api_key_entry = ctk.CTkEntry(
            key_frame,
            placeholder_text="gsk_...",
            font=ctk.CTkFont(size=13),
            fg_color="#313244",
            border_color="#45475a",
            show="*",
            height=36,
        )
        self._api_key_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._show_key_var = ctk.BooleanVar(value=False)
        self._show_key_btn = ctk.CTkButton(
            key_frame, text="Show", width=60, height=36,
            font=ctk.CTkFont(size=12),
            fg_color="#45475a", hover_color="#585b70",
            command=self._toggle_key_visibility,
        )
        self._show_key_btn.pack(side="right")

        ctk.CTkLabel(
            tab,
            text="Get your API key at console.groq.com",
            font=ctk.CTkFont(size=11),
            text_color="#6c7086",
        ).pack(anchor="w", padx=8, pady=(0, 8))

        # Test connection button
        self._test_btn = ctk.CTkButton(
            tab, text="Test Connection",
            font=ctk.CTkFont(size=13),
            fg_color="#45475a", hover_color="#585b70",
            height=32,
            command=self._test_connection,
        )
        self._test_btn.pack(fill="x", padx=8, pady=4)

        self._test_result = ctk.CTkLabel(
            tab, text="",
            font=ctk.CTkFont(size=12),
            text_color="#a6adc8",
            wraplength=WINDOW_WIDTH - 48,
        )
        self._test_result.pack(anchor="w", padx=8, pady=4)

        # API info
        ctk.CTkFrame(tab, height=1, fg_color="#313244").pack(fill="x", padx=8, pady=12)

        info_frame = ctk.CTkFrame(tab, fg_color="#313244", corner_radius=8)
        info_frame.pack(fill="x", padx=8, pady=4)

        info_items = [
            ("Service:", "Groq Cloud"),
            ("Model:", "whisper-large-v3-turbo"),
            ("Format:", "16kHz, mono, 16-bit WAV"),
            ("Max Size:", "25 MB per request"),
        ]
        for label, value in info_items:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(
                row, text=label,
                font=ctk.CTkFont(size=12),
                text_color="#6c7086", width=80, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=value,
                font=ctk.CTkFont(size=12),
                text_color="#cdd6f4", anchor="w",
            ).pack(side="left")

        # Save button
        ctk.CTkButton(
            tab, text="Save API Key",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#22c55e", hover_color="#16a34a",
            text_color="#1e1e2e",
            height=36,
            command=self._save,
        ).pack(fill="x", padx=8, pady=(12, 4))

    # ---- About Tab ----

    def _build_about_tab(self):
        tab = self._tabview.add("About")

        ctk.CTkLabel(
            tab, text="FlowDictation",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#cdd6f4",
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            tab, text="Version 1.0.0",
            font=ctk.CTkFont(size=13),
            text_color="#6c7086",
        ).pack(pady=2)

        ctk.CTkLabel(
            tab, text="Voice dictation powered by Groq Whisper API",
            font=ctk.CTkFont(size=13),
            text_color="#a6adc8",
        ).pack(pady=(2, 16))

        ctk.CTkFrame(tab, height=1, fg_color="#313244").pack(fill="x", padx=24, pady=8)

        usage_text = (
            "How to use:\n\n"
            "1. Set your Groq API key in the API tab\n"
            "2. Hold the hotkey (default: Right Alt)\n"
            "3. Speak your text\n"
            "4. Release the hotkey\n"
            "5. Text is automatically typed at your cursor\n\n"
            "Tip: You can change the hotkey in the General tab.\n"
            "Right-click the tray icon for quick access."
        )

        ctk.CTkLabel(
            tab, text=usage_text,
            font=ctk.CTkFont(size=12),
            text_color="#a6adc8",
            justify="left",
            anchor="nw",
            wraplength=WINDOW_WIDTH - 80,
        ).pack(fill="x", padx=24, pady=8)

    # ---- Handlers ----

    def _on_hotkey_changed(self, choice: str):
        # Map display name back to enum
        for opt in HotkeyOption:
            if opt.display_name == choice:
                self._selected_hotkey = opt
                break
        if self._selected_hotkey == HotkeyOption.CUSTOM:
            self._custom_frame.pack(fill="x", padx=8, pady=4, after=self._hotkey_menu.master)
        else:
            self._custom_frame.pack_forget()

    def _on_volume_changed(self, value: float):
        self._volume_label.configure(text=f"{int(value * 100)}%")

    def _toggle_key_visibility(self):
        if self._show_key_var.get():
            self._api_key_entry.configure(show="*")
            self._show_key_btn.configure(text="Show")
            self._show_key_var.set(False)
        else:
            self._api_key_entry.configure(show="")
            self._show_key_btn.configure(text="Hide")
            self._show_key_var.set(True)

    def _start_recording_hotkey(self):
        if self._recording_custom_hotkey:
            return
        self._recording_custom_hotkey = True
        self._record_btn.configure(text="Press a key...")
        self._custom_label.configure(text="Waiting for key...", text_color="#f97316")

        import keyboard

        def on_key(event):
            if event.event_type == "down":
                keyboard.unhook(hook)
                self._custom_hotkey = CustomHotkeyConfig(
                    key_name=event.name or "",
                    scan_code=event.scan_code,
                    display_name=event.name or f"Key({event.scan_code})",
                )
                self.after(0, self._finish_recording_hotkey)

        hook = keyboard.hook(on_key, suppress=False)

    def _finish_recording_hotkey(self):
        self._recording_custom_hotkey = False
        self._record_btn.configure(text="Record Key")
        if self._custom_hotkey:
            self._custom_label.configure(
                text=f"Custom: {self._custom_hotkey.display_name}",
                text_color="#22c55e",
            )

    def _test_connection(self):
        self._test_btn.configure(state="disabled", text="Testing...")
        self._test_result.configure(text="", text_color="#a6adc8")

        def do_test():
            if self.on_test_connection:
                # Temporarily update API key for testing
                key = self._api_key_entry.get().strip()
                success, msg = self.on_test_connection(key)
                self.after(0, lambda: self._show_test_result(success, msg))
            else:
                self.after(0, lambda: self._show_test_result(False, "No test handler."))

        threading.Thread(target=do_test, daemon=True).start()

    def _show_test_result(self, success: bool, message: str):
        self._test_btn.configure(state="normal", text="Test Connection")
        color = "#22c55e" if success else "#f38ba8"
        self._test_result.configure(text=message, text_color=color)

    def _save(self):
        # Map display name to enum
        hotkey = self._selected_hotkey

        settings = {
            "api_key": self._api_key_entry.get().strip(),
            "selected_hotkey": hotkey,
            "custom_hotkey": self._custom_hotkey,
            "auto_insert_text": self._auto_insert_var.get(),
            "sound_enabled": self._sound_var.get(),
            "sound_volume": self._volume_slider.get(),
            "is_enabled": self._enabled_var.get(),
        }

        if self.on_save:
            self.on_save(settings)

        self.hide()

    def show(self):
        """Show settings window centered on screen."""
        self.deiconify()
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - WINDOW_WIDTH) // 2
        y = (screen_h - WINDOW_HEIGHT) // 2
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        self.lift()
        self.focus_force()

    def hide(self):
        self.withdraw()

    def load_settings(self, api_key: str, selected_hotkey: HotkeyOption,
                      custom_hotkey: Optional[CustomHotkeyConfig],
                      auto_insert: bool, sound_enabled: bool,
                      sound_volume: float, is_enabled: bool):
        """Populate settings from config."""
        self._api_key = api_key
        self._selected_hotkey = selected_hotkey
        self._custom_hotkey = custom_hotkey
        self._auto_insert = auto_insert
        self._sound_enabled = sound_enabled
        self._sound_volume = sound_volume

        # Update UI
        self._api_key_entry.delete(0, "end")
        if api_key:
            self._api_key_entry.insert(0, api_key)

        self._hotkey_menu.set(selected_hotkey.display_name)
        if selected_hotkey == HotkeyOption.CUSTOM:
            self._custom_frame.pack(fill="x", padx=8, pady=4, after=self._hotkey_menu.master)
            if custom_hotkey:
                self._custom_label.configure(
                    text=f"Custom: {custom_hotkey.display_name}",
                    text_color="#22c55e",
                )
        else:
            self._custom_frame.pack_forget()

        self._auto_insert_var.set(auto_insert)
        self._sound_var.set(sound_enabled)
        self._volume_slider.set(sound_volume)
        self._volume_label.configure(text=f"{int(sound_volume * 100)}%")
        self._enabled_var.set(is_enabled)
        self._test_result.configure(text="")
