import json

from app.config import get_settings
from app.gnani import GnaniError, mock
from app.gnani.http import post_gnani


async def transcribe(
    wav_bytes: bytes,
    language: str,
    *,
    keyterms: list[str] | None = None,
    script: str | None = None,
    index: int = 0,
) -> dict:
    settings = get_settings()
    if settings.gnani_mock:
        return mock.transcribe(wav_bytes, language, script=script, index=index)

    form = {
        "model": settings.gnani_stt_model,
        "language_code": language,
        "format": settings.gnani_stt_format,
    }
    if keyterms:
        form["keyterms"] = json.dumps(keyterms, ensure_ascii=False)
    response = await post_gnani(
        settings.gnani_stt_url,
        files={"audio_file": ("segment.wav", wav_bytes, "audio/wav")},
        data=form,
    )
    body = response.json()
    if not body.get("success"):
        raise GnaniError(f"Prisma rejected the audio: {body.get('error', {}).get('type')}")
    return {"text": body.get("transcript") or "", "raw": body}
