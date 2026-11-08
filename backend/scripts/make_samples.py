"""Build the three sample reels in frontend/public/samples.

Run from backend/:
  uv run python -m scripts.make_samples            # placeholder voice-like tones, no credits
  GNANI_MOCK=0 uv run python -m scripts.make_samples --timbre   # real speech from Timbre
"""

import argparse
import asyncio
import subprocess
import tempfile
from pathlib import Path

from app import audio
from app.config import REPO_ROOT, get_settings
from app.gnani import tts
from scripts.speechlike import SAMPLE_RATE, speech_like_pcm, write_wav

OUTPUT = REPO_ROOT / "frontend" / "public" / "samples"
GAP_SEC = 0.8
PLACEHOLDER_BURSTS = [5.0, 5.0, 5.0, 5.0]

SPOKEN_LINES: dict[str, list[str]] = {
    "sample_clean": [
        "इस वीडियो में paid partnership है DemoSkin के साथ।",
        "मैं यह moisturizer तीन हफ़्ते से use कर रही हूँ।",
        "मुझे मेरी skin थोड़ी soft लगी, आपका experience अलग हो सकता है।",
        "Ingredients की list description में है, patch test ज़रूर करना।",
    ],
    "sample_no_disclosure": [
        "Hi guys, आज बात करते हैं इस नए face wash की।",
        "यह 100 percent result देता है, पक्का फ़र्क दिखेगा।",
        "मेरे dermatologist friend ने भी बोला कि यह बिल्कुल safe है।",
        "Link bio में है, offer ख़त्म होने वाला है।",
    ],
    "sample_finance_claims": [
        "दोस्तों, यह sponsored video है DemoFin app के साथ।",
        "इस stock में पैसा double पक्का, zero risk है।",
        "मैं बता रहा हूँ यह stock ख़रीदो, guaranteed return मिलेगा।",
        "अभी app download करो, सिर्फ़ आज free demat account।",
    ],
}


async def timbre_wav(lines: list[str], folder: Path, name: str) -> Path:
    settings = get_settings()
    silence = b"\x00\x00" * int(GAP_SEC * SAMPLE_RATE)
    pcm = silence
    for index, line in enumerate(lines):
        mp3 = folder / f"{name}_{index}.mp3"
        wav = folder / f"{name}_{index}.wav"
        mp3.write_bytes(await tts.speak(line, settings.gnani_tts_voice))
        await asyncio.to_thread(audio.extract_wav, mp3, wav)
        pcm += audio.read_pcm(wav) + silence
    target = folder / f"{name}.wav"
    write_wav(target, pcm)
    return target


def render_reel(wav: Path, target: Path) -> None:
    command = [
        audio.ffmpeg_path(), "-y", "-v", "error", "-i", str(wav),
        "-filter_complex",
        "[0:a]showwaves=s=540x960:mode=cline:rate=15:colors=0xF5A623,format=yuv420p[v]",
        "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(target),
    ]
    subprocess.run(command, check=True, timeout=180)


async def main(use_timbre: bool) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for seed, (name, lines) in enumerate(SPOKEN_LINES.items()):
            if use_timbre:
                wav = await timbre_wav(lines, folder, name)
            else:
                wav = folder / f"{name}.wav"
                write_wav(wav, speech_like_pcm(PLACEHOLDER_BURSTS, GAP_SEC, seed=seed))
            await asyncio.to_thread(render_reel, wav, OUTPUT / f"{name}.mp4")
            print(f"wrote {name}.mp4")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timbre", action="store_true", help="Use real Timbre speech")
    asyncio.run(main(parser.parse_args().timbre))
