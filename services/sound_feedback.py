import os
import threading
import pygame


class SoundFeedback:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._volume = 0.4
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._mixer_ready = False
        self._init_mixer()

    def _init_mixer(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self._mixer_ready = True
            self._load_sounds()
        except Exception:
            self._mixer_ready = False

    def _load_sounds(self):
        sounds_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "sounds")
        for name in ("start", "stop", "success", "error"):
            path = os.path.join(sounds_dir, f"{name}.wav")
            if os.path.exists(path):
                try:
                    self._sounds[name] = pygame.mixer.Sound(path)
                except Exception:
                    pass

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(0.0, min(1.0, value))

    def _play(self, name: str):
        if not self._mixer_ready:
            return
        sound = self._sounds.get(name)
        if sound:
            sound.set_volume(self._volume)
            sound.play()

    def play_start(self):
        self._play("start")

    def play_stop(self):
        self._play("stop")

    def play_success(self):
        self._play("success")

    def play_error(self):
        self._play("error")
