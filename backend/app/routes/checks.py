import asyncio
import json
import re
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session
from sse_starlette.sse import EventSourceResponse
from ulid import ULID

from app.config import get_settings
from app.db import engine, get_session
from app.models import CATEGORIES, TERMINAL_STATUSES, Check, Report, UsageCounter
from app.pipeline import run_check

router = APIRouter(prefix="/api/v1/check", tags=["check"])

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm", ".mp3", ".wav", ".m4a"}
CHUNK_SIZE = 1024 * 1024
SSE_POLL_SECONDS = 0.3
SessionDep = Annotated[Session, Depends(get_session)]


def _require_check(session: Session, check_id: str) -> Check:
    check = session.get(Check, check_id)
    if check is None:
        raise HTTPException(status_code=404, detail="Check not found")
    return check


def _enforce_credit_guard(session: Session) -> None:
    settings = get_settings()
    if settings.gnani_mock or settings.credit_guard_seconds <= 0:
        return
    usage = session.get(UsageCounter, 1)
    if usage and usage.stt_seconds >= settings.credit_guard_seconds:
        raise HTTPException(status_code=429, detail="Demo credit limit reached")


async def _save_upload(file: UploadFile, destination: Path, max_bytes: int) -> None:
    written = 0
    with destination.open("wb") as out:
        while chunk := await file.read(CHUNK_SIZE):
            written += len(chunk)
            if written > max_bytes:
                out.close()
                destination.unlink()
                destination.parent.rmdir()
                raise HTTPException(status_code=413, detail="File too large")
            out.write(chunk)


@router.post("", status_code=202)
async def create_check(
    background: BackgroundTasks,
    session: SessionDep,
    file: Annotated[UploadFile, File()],
    category: Annotated[str, Form()] = "general",
    paid_collab: Annotated[bool, Form()] = False,
    brand: Annotated[str | None, Form(max_length=120)] = None,
    speak_summary: Annotated[bool, Form()] = False,
) -> dict:
    settings = get_settings()
    if category not in CATEGORIES:
        raise HTTPException(status_code=422, detail=f"category must be one of {CATEGORIES}")
    name = Path(file.filename or "").name
    extension = Path(name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Unsupported file type")
    _enforce_credit_guard(session)

    check_id = f"chk_{ULID()}"
    folder = settings.media_dir / check_id
    folder.mkdir(parents=True)
    input_file = f"input{extension}"
    await _save_upload(file, folder / input_file, settings.max_upload_mb * 1024 * 1024)

    session.add(
        Check(
            id=check_id,
            category=category,
            paid_collab=paid_collab,
            brand=(brand or "").strip() or None,
            speak_summary=speak_summary,
            source_name=re.sub(r"[^\w-]", "", Path(name).stem)[:64],
            input_file=input_file,
        )
    )
    session.commit()
    background.add_task(run_check, check_id)
    return {"check_id": check_id, "status": "queued"}


@router.post("/{check_id}/retry", status_code=202)
def retry_check(check_id: str, background: BackgroundTasks, session: SessionDep) -> dict:
    check = _require_check(session, check_id)
    if check.status != "failed":
        raise HTTPException(status_code=409, detail="Only failed checks can be retried")
    _enforce_credit_guard(session)
    check.status, check.stage, check.error, check.report_json = "queued", "queued", None, None
    session.add(check)
    session.commit()
    background.add_task(run_check, check_id)
    return {"check_id": check_id, "status": "queued"}


@router.get("/{check_id}", response_model=Report)
def get_check(check_id: str, session: SessionDep) -> Report:
    check = _require_check(session, check_id)
    if check.report_json:
        return Report.model_validate_json(check.report_json)
    return Report(
        check_id=check.id,
        category=check.category,
        status=check.status,
        stage=check.stage,
        error=check.error,
        media_url=f"/media/{check.id}/{check.input_file}",
    )


def _snapshot(check_id: str) -> dict | None:
    with Session(engine) as session:
        check = session.get(Check, check_id)
        if check is None:
            return None
        return {"status": check.status, "stage": check.stage, "error": check.error}


@router.get("/{check_id}/events")
async def check_events(check_id: str, session: SessionDep) -> EventSourceResponse:
    _require_check(session, check_id)

    async def stream():
        previous = None
        while True:
            snapshot = await run_in_threadpool(_snapshot, check_id)
            if snapshot is None:
                return
            if snapshot != previous:
                previous = snapshot
                yield {"event": "progress", "data": json.dumps(snapshot)}
            if snapshot["status"] in TERMINAL_STATUSES:
                return
            await asyncio.sleep(SSE_POLL_SECONDS)

    return EventSourceResponse(stream())
