import asyncio

from app.config import get_settings
from app.gnani import mock
from app.gnani.http import post_gnani

SUMMARY_LANGUAGE = "hi-IN"


async def speak(text: str, voice: str, language: str = SUMMARY_LANGUAGE) -> bytes:
    settings = get_settings()
    if settings.gnani_mock:
        return await asyncio.to_thread(mock.speak, text, voice)
    response = await post_gnani(
        settings.gnani_tts_url,
        json={
            "text": text,
            "voice": voice,
            "model": settings.gnani_tts_model,
            "language": language,
            "audio_config": {"container": "mp3", "bitrate": "128k"},
        },
    )
    return response.content
