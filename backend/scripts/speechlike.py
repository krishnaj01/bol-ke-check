import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16000
FORMANTS = ((700, 130), (1220, 110), (2600, 170))


def _voiced(seconds: float, rng: np.random.Generator) -> np.ndarray:
    count = int(seconds * SAMPLE_RATE)
    time = np.arange(count) / SAMPLE_RATE
    pitch = 135 + 18 * np.sin(2 * np.pi * 1.7 * time + rng.uniform(0, 6))
    phase = 2 * np.pi * np.cumsum(pitch) / SAMPLE_RATE
    wave_sum = np.zeros(count)
    for harmonic in range(1, 24):
        frequency = 135 * harmonic
        gain = sum(np.exp(-(((frequency - f) / b) ** 2)) for f, b in FORMANTS) + 0.04
        wave_sum += gain * np.sin(harmonic * phase)
    syllables = 0.55 + 0.45 * np.sin(2 * np.pi * 3.6 * time + rng.uniform(0, 6)) ** 2
    return wave_sum * syllables


def speech_like_pcm(bursts: list[float], gap: float, seed: int = 7) -> bytes:
    """Voice-like audio that a VAD treats as speech, with silence between bursts."""
    rng = np.random.default_rng(seed)
    silence = np.zeros(int(gap * SAMPLE_RATE))
    parts = [silence]
    for seconds in bursts:
        parts += [_voiced(seconds, rng), silence]
    signal = np.concatenate(parts)
    signal = signal / np.max(np.abs(signal)) * 0.7
    return (signal * 32767).astype(np.int16).tobytes()


def write_wav(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(SAMPLE_RATE)
        writer.writeframes(pcm)
