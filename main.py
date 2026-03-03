"""FlowDictation Windows - Voice dictation powered by Groq Whisper API.

Hold a hotkey, speak, release — text is transcribed and pasted at your cursor.
"""

import sys
import os
import threading
import customtkinter as ctk

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from models.dictation_state import DictationState, HotkeyOption
from services.dictation_manager import DictationManager
from services.groq_api_client import GroqAPIClient
from views.tray_app import TrayApp
from views.menu_popup import MenuPopup
from views.settings_window import SettingsWindow


def ensure_sounds_exist():
    """Generate sound files if they don't exist yet."""
    sounds_dir = os.path.join(os.path.dirname(__file__), "resources", "sounds")
    if not os.path.exists(os.path.join(sounds_dir, "start.wav")):
        try:
            from scripts.generate_sounds import main as gen_sounds
            gen_sounds()
        except Exception as e:
            print(f"Warning: Could not generate sounds: {e}")


class FlowDictationApp:
    def __init__(self):
        # Generate sound files if needed
        ensure_sounds_exist()

        # Config
        self.config = Config()

        # Hidden root window for tkinter event loop
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.root = ctk.CTk()
        self.root.withdraw()  # hide root window
        self.root.title("FlowDictation")

        # Services
        self.manager = DictationManager(self.config)

        # UI components
        self.tray = TrayApp()
        self.popup = MenuPopup(self.root)
        self.settings_window = SettingsWindow(self.root)

        # Wire everything together
        self._wire_callbacks()

        # Start the dictation manager (hotkey listener)
        self.manager.start()

    def _wire_callbacks(self):
        # --- Dictation Manager -> UI (thread-safe via root.after) ---
        def on_state_changed(state: DictationState, error_msg: str):
            self.root.after(0, lambda: self._handle_state_change(state, error_msg))

        def on_transcription_changed(text: str):
            self.root.after(0, lambda: self.popup.update_transcription(text))

        def on_duration_changed(duration: float):
            self.root.after(0, lambda: self.popup.update_duration(duration))

        self.manager.on_state_changed = on_state_changed
        self.manager.on_transcription_changed = on_transcription_changed
        self.manager.on_duration_changed = on_duration_changed

        # --- Tray -> UI ---
        self.tray.on_left_click = lambda: self.root.after(0, self._toggle_popup)
        self.tray.on_settings_click = lambda: self.root.after(0, self._show_settings)
        self.tray.on_quit_click = lambda: self.root.after(0, self._quit)

        # --- Popup -> App ---
        self.popup.on_copy_click = self._copy_last_transcription
        self.popup.on_toggle_enabled = self._toggle_enabled
        self.popup.on_toggle_sound = self._toggle_sound
        self.popup.on_settings_click = lambda: self.root.after(0, self._show_settings)
        self.popup.on_quit_click = lambda: self.root.after(0, self._quit)

        # --- Settings -> App ---
        self.settings_window.on_save = self._on_settings_save
        self.settings_window.on_test_connection = self._test_api_connection

    def _handle_state_change(self, state: DictationState, error_msg: str):
        self.tray.update_state(state, error_msg)
        self.popup.update_state(state, error_msg)

    def _toggle_popup(self):
        try:
            if self.popup.winfo_viewable():
                self.popup.hide()
            else:
                self.popup.set_enabled(self.manager.is_enabled)
                self.popup.set_sound_enabled(self.config.sound_enabled)
                self.popup.show_near_taskbar()
        except Exception:
            self.popup.show_near_taskbar()

    def _show_settings(self):
        self.settings_window.load_settings(
            api_key=self.config.api_key,
            selected_hotkey=self.config.selected_hotkey,
            custom_hotkey=self.config.custom_hotkey,
            auto_insert=self.config.auto_insert_text,
            sound_enabled=self.config.sound_enabled,
            sound_volume=self.config.sound_volume,
            is_enabled=self.manager.is_enabled,
        )
        self.settings_window.show()

    def _on_settings_save(self, settings: dict):
        self.config.api_key = settings["api_key"]
        self.config.selected_hotkey = settings["selected_hotkey"]
        self.config.custom_hotkey = settings.get("custom_hotkey")
        self.config.auto_insert_text = settings["auto_insert_text"]
        self.config.sound_enabled = settings["sound_enabled"]
        self.config.sound_volume = settings["sound_volume"]
        self.manager.is_enabled = settings.get("is_enabled", True)
        self.manager.reload_config()

    def _test_api_connection(self, api_key: str) -> tuple[bool, str]:
        client = GroqAPIClient(api_key)
        return client.test_connection()

    def _copy_last_transcription(self):
        if self.manager.last_transcription:
            import pyperclip
            try:
                pyperclip.copy(self.manager.last_transcription)
            except Exception:
                pass

    def _toggle_enabled(self, enabled: bool):
        self.manager.is_enabled = enabled

    def _toggle_sound(self, enabled: bool):
        self.config.sound_enabled = enabled

    def _quit(self):
        self.manager.stop()
        self.tray.stop()
        self.root.after(100, self.root.destroy)

    def run(self):
        """Run the application. Tray on daemon thread, tkinter on main thread."""
        # Start tray icon on daemon thread
        tray_thread = threading.Thread(target=self.tray.run, daemon=True)
        tray_thread.start()

        # Run tkinter mainloop on main thread
        self.root.mainloop()


def main():
    app = FlowDictationApp()
    app.run()


if __name__ == "__main__":
    main()
