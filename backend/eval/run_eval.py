"""Measure Bol Ke Check on labelled clips (SPEC section 8).

Run from backend/:
  uv run python -m eval.run_eval --split test     # real run, needs GNANI_MOCK=0 and clips
  GNANI_MOCK=1 uv run python -m eval.run_eval --dry-run   # tests the plumbing, not accuracy

Only real runs are published to media/eval, which the About page reads.
"""

import argparse
import asyncio
import html
import json
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session
from ulid import ULID

from app.config import BACKEND_ROOT, get_settings
from app.db import engine, init_db
from app.gnani import mock
from app.models import Check, EvalRun, Report
from app.pipeline import run_check
from eval.metrics import ClipResult, Violation, compute_metrics
from scripts.speechlike import speech_like_pcm, write_wav

DATASET = BACKEND_ROOT / "eval" / "dataset"
OUTPUT = BACKEND_ROOT / "eval" / "output"
DRY_RUN_BURST_SEC = 5.0
DRY_RUN_GAP_SEC = 0.8


def load_labels(path: Path, split: str) -> list[dict]:
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return [row for row in rows if row.get("split") == split]


def build_dry_run_clips(folder: Path) -> list[dict]:
    """Turn the dev scripts into placeholder audio with mock transcripts."""
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    lines = (DATASET / "dev_scripts.jsonl").read_text(encoding="utf-8").splitlines()
    for script in map(json.loads, filter(None, lines)):
        spoken = script["lines"]
        wav = folder / f"{script['clip_id']}.wav"
        write_wav(wav, speech_like_pcm([DRY_RUN_BURST_SEC] * len(spoken), DRY_RUN_GAP_SEC))
        mock.SCRIPTS[script["clip_id"]] = [line["text"] for line in spoken]
        violations = [
            {
                "family": line["violation"],
                "time_sec": DRY_RUN_GAP_SEC + index * (DRY_RUN_BURST_SEC + DRY_RUN_GAP_SEC) + 1,
            }
            for index, line in enumerate(spoken)
            if line.get("violation")
        ]
        if script["paid_collab"] and not script["disclosed"]:
            violations.append({"family": "missing_disclosure", "time_sec": None})
        rows.append({**script, "file": str(wav), "violations": violations})
    return rows


async def evaluate_clip(row: dict) -> ClipResult:
    settings = get_settings()
    source = Path(row["file"])
    if not source.is_absolute():
        source = DATASET / source
    check_id = f"chk_{ULID()}"
    folder = settings.media_dir / check_id
    folder.mkdir(parents=True)
    input_file = f"input{source.suffix.lower()}"
    shutil.copy(source, folder / input_file)
    with Session(engine) as session:
        session.add(
            Check(
                id=check_id,
                category=row["category"],
                paid_collab=row["paid_collab"],
                source_name=row["clip_id"],
                input_file=input_file,
            )
        )
        session.commit()

    started = time.perf_counter()
    await run_check(check_id)
    latency = time.perf_counter() - started

    with Session(engine) as session:
        check = session.get(Check, check_id)
        report = Report.model_validate_json(check.report_json) if check.report_json else None
        status = check.status
    shutil.rmtree(folder)
    return ClipResult(
        clip_id=row["clip_id"],
        paid_collab=row["paid_collab"],
        disclosed=row.get("disclosed", False),
        violations=[Violation(**violation) for violation in row["violations"]],
        flags=report.flags if report else [],
        disclosure=report.disclosure if report else None,
        duration_sec=report.duration_sec or 0.0 if report else 0.0,
        latency_sec=latency,
        status=status,
    )


def render_html(metrics: dict) -> str:
    rows = "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in metrics.items()
    )
    return f"<!doctype html><meta charset=utf-8><title>Eval</title><table>{rows}</table>"


def write_outputs(metrics: dict, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (destination / "metrics.html").write_text(render_html(metrics), encoding="utf-8")


async def main(split: str, dry_run: bool) -> int:
    settings = get_settings()
    if dry_run and not settings.gnani_mock:
        print("--dry-run needs GNANI_MOCK=1.")
        return 2
    if not dry_run and settings.gnani_mock:
        print("A real evaluation needs GNANI_MOCK=0. Use --dry-run to test the plumbing.")
        return 2

    init_db()
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    rows = (
        build_dry_run_clips(OUTPUT / "dry_run_clips")
        if dry_run
        else load_labels(DATASET / "labels.jsonl", split)
    )
    if not rows:
        print(f"No clips labelled split={split} in eval/dataset/labels.jsonl. Nothing measured.")
        return 1

    results = [await evaluate_clip(row) for row in rows]
    metrics = {
        "mode": "mock" if dry_run else "real",
        "dataset_version": "dev-dry-run" if dry_run else split,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        **compute_metrics(results),
    }
    write_outputs(metrics, OUTPUT)
    if not dry_run:
        write_outputs(metrics, settings.media_dir / "eval")
        with Session(engine) as session:
            session.add(EvalRun(dataset_version=split, metrics_json=json.dumps(metrics)))
            session.commit()
    print(json.dumps(metrics, indent=2))
    if dry_run:
        print("Dry run: mock transcripts. These numbers say nothing about real accuracy.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["test", "dev"], default="test")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    sys.exit(asyncio.run(main(arguments.split, arguments.dry_run)))
