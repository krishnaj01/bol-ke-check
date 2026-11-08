import io
import shutil
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import webrtcvad

SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2
FRAME_MS = 30
FRAME_BYTES = int(SAMPLE_RATE * FRAME_MS / 1000) * SAMPLE_WIDTH
VAD_AGGRESSIVENESS = 2

MIN_SEGMENT_SEC = 3.0
# Prisma REST accepts at most 30 s per request.
MAX_SEGMENT_SEC = 12.0
CLOSE_GAP_SEC = 0.3
JOIN_SHORT_GAP_SEC = 1.0
MIN_REGION_SEC = 0.25
PADDING_SEC = 0.15

Span = tuple[float, float]


class MediaError(Exception):
    """ffmpeg could not read the uploaded file."""


def ffmpeg_path() -> str:
    return shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()


def extract_wav(source: Path, target: Path) -> None:
    command = [
        ffmpeg_path(), "-y", "-v", "error", "-i", str(source),
        "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(target),
    ]
    try:
        subprocess.run(command, capture_output=True, check=True, timeout=120)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise MediaError(str(exc)) from exc


def read_pcm(path: Path) -> bytes:
    with wave.open(str(path), "rb") as reader:
        return reader.readframes(reader.getnframes())


def duration_of(pcm: bytes) -> float:
    return len(pcm) / (SAMPLE_RATE * SAMPLE_WIDTH)


def voiced_regions(pcm: bytes) -> list[Span]:
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    frame_sec = FRAME_MS / 1000
    regions: list[Span] = []
    start: float | None = None
    usable = len(pcm) - len(pcm) % FRAME_BYTES
    for index, offset in enumerate(range(0, usable, FRAME_BYTES)):
        at = index * frame_sec
        if vad.is_speech(pcm[offset : offset + FRAME_BYTES], SAMPLE_RATE):
            start = at if start is None else start
        elif start is not None:
            regions.append((start, at))
            start = None
    if start is not None:
        regions.append((start, usable / FRAME_BYTES * frame_sec))
    return regions


def merge_regions(regions: list[Span]) -> list[Span]:
    merged: list[Span] = []
    for start, end in regions:
        if merged:
            previous_start, previous_end = merged[-1]
            gap = start - previous_end
            too_short = previous_end - previous_start < MIN_SEGMENT_SEC
            joinable = gap <= CLOSE_GAP_SEC or (too_short and gap <= JOIN_SHORT_GAP_SEC)
            if joinable and end - previous_start <= MAX_SEGMENT_SEC:
                merged[-1] = (previous_start, end)
                continue
        merged.append((start, end))
    return [span for span in merged if span[1] - span[0] >= MIN_REGION_SEC]


def split_long(spans: list[Span]) -> list[Span]:
    result: list[Span] = []
    for start, end in spans:
        length = end - start
        pieces = max(1, int(length // MAX_SEGMENT_SEC) + (length % MAX_SEGMENT_SEC > 0))
        width = length / pieces
        result.extend((start + i * width, start + (i + 1) * width) for i in range(pieces))
    return result


def speech_segments(pcm: bytes) -> list[Span]:
    duration = duration_of(pcm)
    spans = split_long(merge_regions(voiced_regions(pcm)))
    return [
        (round(max(0.0, start - PADDING_SEC), 2), round(min(duration, end + PADDING_SEC), 2))
        for start, end in spans
    ]


def slice_wav(pcm: bytes, span: Span) -> bytes:
    start = int(span[0] * SAMPLE_RATE) * SAMPLE_WIDTH
    end = int(span[1] * SAMPLE_RATE) * SAMPLE_WIDTH
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(SAMPLE_WIDTH)
        writer.setframerate(SAMPLE_RATE)
        writer.writeframes(pcm[start:end])
    return buffer.getvalue()
