"""One real Timbre call and one real Prisma call. Uses a few credits.

Run from backend/: GNANI_MOCK=0 uv run python -m scripts.smoke_gnani
"""

import asyncio
import sys
import tempfile
from pathlib import Path

from app import audio
from app.config import get_settings
from app.gnani import GnaniError, stt, tts

LINE = "इस सीरम से सात दिन में guaranteed glow मिलेगा।"


async def main() -> int:
    settings = get_settings()
    if settings.gnani_mock:
        print("GNANI_MOCK is on. Re-run with GNANI_MOCK=0.")
        return 2
    with tempfile.TemporaryDirectory() as folder:
        mp3 = Path(folder) / "line.mp3"
        wav = Path(folder) / "line.wav"
        try:
            mp3.write_bytes(await tts.speak(LINE, settings.gnani_tts_voice))
            print(f"Timbre OK: {mp3.stat().st_size} bytes of MP3")
            await asyncio.to_thread(audio.extract_wav, mp3, wav)
            result = await stt.transcribe(wav.read_bytes(), "hi-IN")
        except GnaniError as error:
            print(f"FAILED: {error}")
            return 1
    print(f"Prisma OK ({result['raw'].get('model')}): {result['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
