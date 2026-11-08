from app.config import get_settings
from app.gnani import GnaniError, mock


async def transcribe(
    wav_bytes: bytes,
    language: str,
    *,
    keyterms: list[str] | None = None,
    script: str | None = None,
    index: int = 0,
) -> dict:
    if get_settings().gnani_mock:
        return mock.transcribe(wav_bytes, language, script=script, index=index)
    raise GnaniError("Prisma client not configured")
