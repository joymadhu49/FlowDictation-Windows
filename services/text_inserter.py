import time
import threading
import pyperclip
import keyboard


class TextInserter:
    def insert(self, text: str):
        """Insert text at cursor by copying to clipboard and simulating Ctrl+V.
        Restores the previous clipboard content after a delay."""
        # Save current clipboard
        try:
            previous = pyperclip.paste()
        except Exception:
            previous = ""

        # Set new text to clipboard
        try:
            pyperclip.copy(text)
        except Exception:
            return

        # Small delay to ensure clipboard is ready
        time.sleep(0.05)

        # Simulate Ctrl+V paste
        try:
            keyboard.send("ctrl+v")
        except Exception:
            pass

        # Restore clipboard after delay on background thread
        def restore():
            time.sleep(1.0)
            try:
                pyperclip.copy(previous)
            except Exception:
                pass

        threading.Thread(target=restore, daemon=True).start()

    def copy_only(self, text: str):
        """Just copy text to clipboard without pasting."""
        try:
            pyperclip.copy(text)
        except Exception:
            pass
