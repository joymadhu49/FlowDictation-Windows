import os
import requests

API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
MODEL = "whisper-large-v3-turbo"
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


class GroqAPIError(Exception):
    pass


class GroqAPIClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file via Groq Whisper API. Returns transcription text."""
        if not self.api_key:
            raise GroqAPIError("Missing API key. Set your Groq API key in Settings.")

        if not os.path.exists(audio_path):
            raise GroqAPIError("Audio file not found.")

        file_size = os.path.getsize(audio_path)
        if file_size > MAX_FILE_SIZE:
            raise GroqAPIError("Audio file too large (max 25 MB).")

        if file_size == 0:
            raise GroqAPIError("Audio file is empty.")

        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            with open(audio_path, "rb") as f:
                files = {"file": ("audio.wav", f, "audio/wav")}
                data = {
                    "model": MODEL,
                    "response_format": "json",
                    "language": "en",
                }
                response = requests.post(
                    API_URL, headers=headers, files=files, data=data, timeout=30
                )
        except requests.ConnectionError:
            raise GroqAPIError("Connection failed. Check your internet connection.")
        except requests.Timeout:
            raise GroqAPIError("Request timed out. Please try again.")
        except requests.RequestException as e:
            raise GroqAPIError(f"Request failed: {e}")

        if response.status_code == 200:
            try:
                result = response.json()
                text = result.get("text", "").strip()
                if not text:
                    raise GroqAPIError("Empty transcription returned.")
                return text
            except (ValueError, KeyError):
                raise GroqAPIError("Invalid response from API.")

        if response.status_code == 401:
            raise GroqAPIError("Invalid API key. Check your Groq API key in Settings.")
        if response.status_code == 413:
            raise GroqAPIError("Audio file too large for API.")
        if response.status_code == 429:
            raise GroqAPIError("Rate limited. Please wait and try again.")

        # Try to extract error message from response
        try:
            error_data = response.json()
            msg = error_data.get("error", {}).get("message", "")
            if msg:
                raise GroqAPIError(f"API error ({response.status_code}): {msg}")
        except (ValueError, AttributeError):
            pass

        raise GroqAPIError(f"API error (HTTP {response.status_code}).")

    def test_connection(self) -> tuple[bool, str]:
        """Test API connection. Returns (success, message)."""
        if not self.api_key:
            return False, "No API key configured."

        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers,
                timeout=10,
            )
            if response.status_code == 200:
                return True, "Connection successful! API key is valid."
            if response.status_code == 401:
                return False, "Invalid API key."
            return False, f"Unexpected response (HTTP {response.status_code})."
        except requests.ConnectionError:
            return False, "Connection failed. Check your internet."
        except requests.Timeout:
            return False, "Connection timed out."
        except requests.RequestException as e:
            return False, f"Connection error: {e}"
