"""Generate WAV sound effects for FlowDictation using numpy."""

import os
import wave
import struct
import math

SAMPLE_RATE = 44100


def generate_tone(frequency: float, duration: float, volume: float = 0.5,
                  fade_in: float = 0.01, fade_out: float = 0.05) -> list[int]:
    """Generate a sine wave tone with fade in/out."""
    num_samples = int(SAMPLE_RATE * duration)
    fade_in_samples = int(SAMPLE_RATE * fade_in)
    fade_out_samples = int(SAMPLE_RATE * fade_out)
    samples = []

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        sample = math.sin(2 * math.pi * frequency * t) * volume

        # Fade in
        if i < fade_in_samples:
            sample *= i / fade_in_samples
        # Fade out
        if i > num_samples - fade_out_samples:
            remaining = num_samples - i
            sample *= remaining / fade_out_samples

        samples.append(int(sample * 32767))

    return samples


def mix_tones(*tone_lists: list[int]) -> list[int]:
    """Mix multiple tone lists by averaging."""
    max_len = max(len(t) for t in tone_lists)
    result = [0] * max_len
    for tones in tone_lists:
        for i, s in enumerate(tones):
            result[i] += s
    count = len(tone_lists)
    return [s // count for s in result]


def write_wav(filename: str, samples: list[int]):
    """Write samples to a WAV file."""
    with wave.open(filename, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        data = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(data)


def generate_start_sound() -> list[int]:
    """Rising two-tone chime — recording starts."""
    tone1 = generate_tone(880, 0.08, 0.4, fade_in=0.005, fade_out=0.02)
    silence = [0] * int(SAMPLE_RATE * 0.03)
    tone2 = generate_tone(1175, 0.1, 0.4, fade_in=0.005, fade_out=0.04)
    return tone1 + silence + tone2


def generate_stop_sound() -> list[int]:
    """Soft descending pop — recording stops."""
    tone = generate_tone(660, 0.1, 0.35, fade_in=0.005, fade_out=0.06)
    return tone


def generate_success_sound() -> list[int]:
    """Pleasant ascending chord — transcription succeeded."""
    tone1 = generate_tone(523, 0.12, 0.3, fade_in=0.005, fade_out=0.03)
    silence = [0] * int(SAMPLE_RATE * 0.02)
    tone2 = generate_tone(659, 0.12, 0.3, fade_in=0.005, fade_out=0.03)
    silence2 = [0] * int(SAMPLE_RATE * 0.02)
    tone3 = generate_tone(784, 0.15, 0.3, fade_in=0.005, fade_out=0.06)
    return tone1 + silence + tone2 + silence2 + tone3


def generate_error_sound() -> list[int]:
    """Low descending buzz — error occurred."""
    tone1 = generate_tone(330, 0.15, 0.4, fade_in=0.005, fade_out=0.03)
    silence = [0] * int(SAMPLE_RATE * 0.05)
    tone2 = generate_tone(220, 0.2, 0.4, fade_in=0.005, fade_out=0.08)
    return tone1 + silence + tone2


def main():
    sounds_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "sounds")
    os.makedirs(sounds_dir, exist_ok=True)

    sounds = {
        "start": generate_start_sound(),
        "stop": generate_stop_sound(),
        "success": generate_success_sound(),
        "error": generate_error_sound(),
    }

    for name, samples in sounds.items():
        path = os.path.join(sounds_dir, f"{name}.wav")
        write_wav(path, samples)
        print(f"Generated: {path}")

    print("All sound files generated successfully.")


if __name__ == "__main__":
    main()
