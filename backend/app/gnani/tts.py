import asyncio

from app.config import get_settings
from app.gnani import GnaniError, mock


async def speak(text: str, voice: str) -> bytes:
    if get_settings().gnani_mock:
        return await asyncio.to_thread(mock.speak, text, voice)
    raise GnaniError("Timbre client not configured")
