import asyncio
import hashlib
import json
import logging
from pathlib import Path

from sqlmodel import Session

from app import audio, review, rules_engine, scoring, summary
from app.config import get_settings
from app.db import engine
from app.gnani import GnaniError, stt
from app.models import (
    AUDIO_LANGUAGES,
    Check,
    ErrorCode,
    Report,
    Segment,
    TranscriptCache,
    UsageCounter,
)

logger = logging.getLogger(__name__)

STT_CONCURRENCY = 4


class PipelineError(Exception):
    def __init__(self, code: ErrorCode, detail: str = "") -> None:
        super().__init__(detail or code)
        self.code: ErrorCode = code


def _load(check_id: str) -> Check:
    with Session(engine) as session:
        check = session.get(Check, check_id)
        session.expunge(check)
        return check


def _update(check_id: str, **fields) -> None:
    with Session(engine) as session:
        check = session.get(Check, check_id)
        for key, value in fields.items():
            setattr(check, key, value)
        session.add(check)
        session.commit()


def _cached_transcript(sha: str, language: str) -> str | None:
    with Session(engine) as session:
        row = session.get(TranscriptCache, (sha, language))
        return row.text if row else None


def _store_transcript(sha: str, language: str, text: str, raw: dict, seconds: float) -> None:
    with Session(engine) as session:
        session.merge(
            TranscriptCache(
                audio_sha256=sha,
                language=language,
                text=text,
                provider_raw_json=json.dumps(raw, ensure_ascii=False),
            )
        )
        usage = session.get(UsageCounter, 1) or UsageCounter(id=1)
        usage.stt_seconds += seconds
        session.add(usage)
        session.commit()


async def extract_stage(check: Check, folder: Path) -> tuple[bytes, float]:
    target = folder / "audio.wav"
    try:
        await asyncio.to_thread(audio.extract_wav, folder / check.input_file, target)
    except audio.MediaError as error:
        raise PipelineError("bad_media", str(error)) from error
    pcm = await asyncio.to_thread(audio.read_pcm, target)
    duration = round(audio.duration_of(pcm), 2)
    if duration > get_settings().max_audio_sec:
        raise PipelineError("too_long")
    return pcm, duration


async def transcribe_stage(check: Check, pcm: bytes) -> list[Segment]:
    settings = get_settings()
    spans = await asyncio.to_thread(audio.speech_segments, pcm)
    if not spans:
        raise PipelineError("no_speech")
    language = AUDIO_LANGUAGES[check.language]
    cache_scope = f"{language}:{settings.gnani_stt_model}:{settings.gnani_stt_format}"
    keyterms = rules_engine.keyterms_for(check.category) if settings.gnani_stt_keyterms else None
    gate = asyncio.Semaphore(STT_CONCURRENCY)

    async def transcribe_one(index: int, span: audio.Span) -> Segment:
        wav = audio.slice_wav(pcm, span)
        sha = hashlib.sha256(wav).hexdigest()
        text = None if settings.gnani_mock else _cached_transcript(sha, cache_scope)
        if text is None:
            async with gate:
                result = await stt.transcribe(
                    wav, language, keyterms=keyterms, script=check.source_name, index=index
                )
            text = result["text"].strip()
            if not settings.gnani_mock:
                _store_transcript(sha, cache_scope, text, result["raw"], span[1] - span[0])
        return Segment(id=f"s{index + 1}", start_sec=span[0], end_sec=span[1], text=text)

    try:
        segments = await asyncio.gather(*(transcribe_one(i, s) for i, s in enumerate(spans)))
    except GnaniError as error:
        raise PipelineError("gnani_failed", str(error)) from error
    spoken = [segment for segment in segments if segment.text]
    if not spoken:
        raise PipelineError("no_speech")
    return spoken


async def _execute(check_id: str) -> None:
    check = _load(check_id)
    folder = get_settings().media_dir / check_id

    _update(check_id, stage="extract")
    pcm, duration = await extract_stage(check, folder)

    _update(check_id, status="transcribing", stage="transcribe", duration_sec=duration)
    segments = await transcribe_stage(check, pcm)

    _update(check_id, status="reviewing", stage="rules")
    scan = rules_engine.scan(segments, check.category, check.paid_collab, duration)

    _update(check_id, stage="review")
    outcome = await review.review_transcript(segments, check.category, check.brand, scan.flags)

    _update(check_id, stage="summary")
    flags = sorted(outcome.flags, key=lambda flag: flag.start_sec)
    score = scoring.risk_score(flags)
    level = scoring.risk_level(score)
    summary_text = summary.build_display(flags, score, level, scan.disclosure)
    audio_url = None
    if check.speak_summary:
        spoken = summary.build_spoken(flags, score, level, scan.disclosure)
        if await summary.synthesise(spoken, folder / "summary.mp3"):
            audio_url = f"/media/{check_id}/summary.mp3"

    status = "partial" if outcome.partial else "complete"
    report = Report(
        check_id=check_id,
        category=check.category,
        language=check.language,
        risk_score=score,
        risk_level=level,
        duration_sec=duration,
        disclosure=scan.disclosure,
        flags=flags,
        segments=segments,
        summary_hi=summary_text,
        summary_audio_url=audio_url,
        media_url=f"/media/{check_id}/{check.input_file}",
        status=status,
        stage="done",
    )
    _update(
        check_id,
        status=status,
        stage="done",
        risk_score=score,
        risk_level=level,
        report_json=report.model_dump_json(),
    )


async def run_check(check_id: str) -> None:
    try:
        await _execute(check_id)
    except PipelineError as error:
        logger.warning("Check %s failed: %s", check_id, error)
        _update(check_id, status="failed", stage="done", error=error.code)
    except Exception:
        logger.exception("Check %s crashed", check_id)
        _update(check_id, status="failed", stage="done", error="internal")
