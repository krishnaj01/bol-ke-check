"""Generate labelled clips with Timbre from a scripts file, optionally mixed with music.

Run from backend/:
  GNANI_MOCK=0 uv run python -m eval.make_synthetic --scripts eval/dataset/dev_scripts.jsonl --split dev
  GNANI_MOCK=0 uv run python -m eval.make_synthetic --scripts eval/dataset/test_scripts.jsonl \\
      --split test --music path/to/royalty_free.mp3

Each script line is one JSON object:
  {"clip_id", "category", "paid_collab", "disclosed", "voice"?, "language"?,
   "lines": [{"text": "...", "violation": "<family>"?}]}
Appends to eval/dataset/labels.jsonl. Add self-recorded clips to that file by hand.
"""

import argparse
import asyncio
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from app import audio, summary
from app.config import BACKEND_ROOT, get_settings
from scripts.speechlike import SAMPLE_RATE, write_wav

DATASET = BACKEND_ROOT / "eval" / "dataset"
CLIPS = DATASET / "clips"
LABELS = DATASET / "labels.jsonl"
PAUSE_SEC = 0.6
MUSIC_VOLUMES = (0.08, 0.15, 0.25)


def mix_music(voice: Path, music: Path, target: Path, volume: float) -> None:
    command = [
        audio.ffmpeg_path(), "-y", "-v", "error", "-i", str(voice),
        "-stream_loop", "-1", "-i", str(music),
        "-filter_complex",
        f"[1:a]volume={volume}[m];[0:a][m]amix=inputs=2:duration=first:normalize=0",
        "-ac", "1", "-ar", str(SAMPLE_RATE), str(target),
    ]
    subprocess.run(command, check=True, timeout=120)


async def synthesise_clip(script: dict, folder: Path) -> tuple[Path, list[dict]]:
    settings = get_settings()
    voice = script.get("voice", settings.gnani_tts_voice)
    language = script.get("language", "hi-IN")
    pause = b"\x00\x00" * int(PAUSE_SEC * SAMPLE_RATE)
    pcm = pause
    violations = []
    for index, line in enumerate(script["lines"]):
        mp3 = folder / f"line_{index}.mp3"
        wav = folder / f"line_{index}.wav"
        mp3.write_bytes(await summary.cached_speech(line["text"], voice, language))
        await asyncio.to_thread(audio.extract_wav, mp3, wav)
        speech = audio.read_pcm(wav)
        if line.get("violation"):
            violations.append(
                {
                    "family": line["violation"],
                    "time_sec": round(audio.duration_of(pcm) + audio.duration_of(speech) / 2, 2),
                }
            )
        pcm += speech + pause
    target = folder / "clip.wav"
    write_wav(target, pcm)
    return target, violations


async def main(scripts: Path, split: str, music: Path | None, seed: int) -> int:
    if get_settings().gnani_mock:
        print("make_synthetic calls Timbre. Re-run with GNANI_MOCK=0.")
        return 2
    rng = random.Random(seed)
    CLIPS.mkdir(parents=True, exist_ok=True)
    known = LABELS.read_text(encoding="utf-8") if LABELS.exists() else ""
    with LABELS.open("a", encoding="utf-8") as labels:
        for raw in filter(None, scripts.read_text(encoding="utf-8").splitlines()):
            script = json.loads(raw)
            clip_id = script["clip_id"]
            if f'"clip_id": "{clip_id}"' in known:
                print(f"skip {clip_id}, already labelled")
                continue
            with tempfile.TemporaryDirectory() as tmp:
                wav, violations = await synthesise_clip(script, Path(tmp))
                target = CLIPS / f"{clip_id}.wav"
                volume = None
                if music:
                    volume = rng.choice(MUSIC_VOLUMES)
                    await asyncio.to_thread(mix_music, wav, music, target, volume)
                else:
                    target.write_bytes(wav.read_bytes())
            if script["paid_collab"] and not script["disclosed"]:
                violations.append({"family": "missing_disclosure", "time_sec": None})
            row = {
                "clip_id": clip_id,
                "split": split,
                "source": "timbre",
                "music_volume": volume,
                "category": script["category"],
                "paid_collab": script["paid_collab"],
                "disclosed": script["disclosed"],
                "file": f"clips/{clip_id}.wav",
                "violations": violations,
            }
            labels.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"wrote {clip_id}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scripts", type=Path, required=True)
    parser.add_argument("--split", choices=["test", "dev"], required=True)
    parser.add_argument("--music", type=Path)
    parser.add_argument("--seed", type=int, default=7)
    arguments = parser.parse_args()
    sys.exit(asyncio.run(main(arguments.scripts, arguments.split, arguments.music, arguments.seed)))
