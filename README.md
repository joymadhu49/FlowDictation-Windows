# FlowDictation Windows

Voice dictation app for Windows powered by Groq Whisper API — hold a hotkey, speak, release to transcribe and auto-paste text at your cursor.

> Python port of the macOS [FlowDictation](https://github.com/joymadhu49/FlowDictation) app.

## Features

- **Hold-to-record** — hold a hotkey, speak, release to transcribe
- **Auto-paste** — transcribed text is automatically typed at your cursor
- **System tray** — colored microphone icon shows status (green/red/orange/yellow)
- **Settings UI** — modern dark-themed settings with 3 tabs
- **Sound feedback** — audio cues for recording start, stop, success, and errors
- **Customizable hotkey** — Right Alt, Alt, Control, Right Shift, or any custom key
- **Portable .exe** — build a single-file executable with PyInstaller

## Quick Start

### Option 1: Run from source

```bash
git clone https://github.com/joymadhu49/FlowDictation-Windows.git
cd FlowDictation-Windows
pip install -r requirements.txt
python main.py
```

### Option 2: Build a portable .exe

```bash
scripts\build.bat
```

Then run `dist\FlowDictation.exe` — single file, no Python needed.

## First-Time Setup

1. A green microphone icon appears in your system tray
2. Right-click tray icon → **Settings** → **API** tab
3. Enter your Groq API key (get one at [console.groq.com](https://console.groq.com))
4. Click **Test Connection** to verify
5. Click **Save API Key**

## Usage

1. **Hold Right Alt** (default hotkey)
2. Speak your text
3. **Release Right Alt**
4. Text gets transcribed and pasted at your cursor

Left-click the tray icon to see last transcription, toggle sound, or enable/disable.

## Hotkey Options

Change the hotkey in Settings → General tab:

| Hotkey | Description |
|--------|-------------|
| **Right Alt** | Default, least likely to conflict |
| **Alt (Either)** | Left or right Alt key |
| **Control** | Ctrl key |
| **Right Shift** | Right Shift key |
| **Custom** | Record any key you want |

## Project Structure

```
FlowDictation-Windows/
├── main.py                        # Entry point
├── config.py                      # Settings persistence (JSON in %APPDATA%)
├── FlowDictation.spec             # PyInstaller build spec
├── requirements.txt               # Python dependencies
├── models/
│   └── dictation_state.py         # DictationState, HotkeyOption enums
├── services/
│   ├── dictation_manager.py       # Central orchestrator / state machine
│   ├── groq_api_client.py         # Groq Whisper API client
│   ├── audio_recorder.py          # Audio recording (sounddevice)
│   ├── global_hotkey_manager.py   # Global hotkey detection (keyboard)
│   ├── text_inserter.py           # Clipboard + Ctrl+V paste
│   └── sound_feedback.py          # Sound playback (pygame)
├── views/
│   ├── tray_app.py                # System tray icon (pystray + Pillow)
│   ├── menu_popup.py              # Status popup window (customtkinter)
│   └── settings_window.py         # Settings UI with 3 tabs
├── resources/
│   └── sounds/                    # Generated WAV sound files
└── scripts/
    ├── generate_sounds.py         # Generate sound effects
    └── build.bat                  # PyInstaller build script
```

## Dependencies

| Library | Purpose |
|---------|---------|
| `requests` | Groq API HTTP client |
| `sounddevice` + `numpy` | Audio recording (16kHz, mono, 16-bit WAV) |
| `pystray` + `Pillow` | System tray icon with colored status indicators |
| `customtkinter` | Modern settings UI + popup window |
| `keyboard` | Global hotkey detection (key down/up events) |
| `pyperclip` | Clipboard read/write |
| `pygame` | Sound playback with volume control |

## Note

The `keyboard` library requires **admin/elevated privileges** on some Windows setups for global hotkey detection. If hotkeys don't work, try running as Administrator.

## License

MIT
