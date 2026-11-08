import hashlib
import logging
from pathlib import Path

from app.config import get_settings
from app.gnani import GnaniError, tts
from app.models import Disclosure, Flag, RiskLevel

logger = logging.getLogger(__name__)

SPOKEN_LEVEL = {"high": "ज़्यादा", "medium": "मध्यम", "low": "कम"}
ROMAN_LEVEL = {"high": "zyada", "medium": "madhyam", "low": "kam"}


def _clock(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def _timed(flags: list[Flag]) -> list[Flag]:
    return [flag for flag in sorted(flags, key=lambda f: f.start_sec)
            if flag.family != "missing_disclosure"]


def build_display(flags: list[Flag], score: int, level: RiskLevel, disclosure: Disclosure) -> str:
    parts = []
    timed = _timed(flags)
    if timed:
        parts.append(f"Is video mein {len(timed)} jagah risk hai.")
        parts.append(f"Pehla flag {_clock(timed[0].start_sec)} par hai.")
    else:
        parts.append("Is video ki boli hui lines mein koi risk nahi mila.")
    if disclosure.required and not disclosure.found:
        parts.append("Paid partnership ka zikr video mein nahi mila.")
    parts.append(f"Risk score 100 mein se {score} hai, level {ROMAN_LEVEL[level]}.")
    parts.append("Ye automated pre-check hai, legal advice nahi.")
    return " ".join(parts)


def build_spoken(flags: list[Flag], score: int, level: RiskLevel, disclosure: Disclosure) -> str:
    parts = []
    timed = _timed(flags)
    if timed:
        start = int(timed[0].start_sec)
        parts.append(f"इस वीडियो में {len(timed)} जगह रिस्क है।")
        parts.append(
            f"पहला फ्लैग {start // 60} मिनट {start % 60} सेकंड पर है।"
        )
    else:
        parts.append("इस वीडियो की बोली हुई लाइनों में कोई रिस्क नहीं मिला।")
    if disclosure.required and not disclosure.found:
        parts.append("पेड पार्टनरशिप का ज़िक्र वीडियो में नहीं मिला।")
    parts.append(f"रिस्क स्कोर 100 में से {score} है, स्तर {SPOKEN_LEVEL[level]}।")
    parts.append("यह ऑटोमेटेड प्री-चेक है, कानूनी सलाह नहीं।")
    return " ".join(parts)


async def synthesise(spoken: str, target: Path) -> bool:
    settings = get_settings()
    voice = settings.gnani_tts_voice
    key = hashlib.sha256(f"{settings.gnani_tts_model}:{voice}:{spoken}".encode()).hexdigest()
    cache = settings.media_dir / "_tts_cache" / f"{key}.mp3"
    try:
        if not cache.exists():
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(await tts.speak(spoken, voice))
    except GnaniError as error:
        logger.warning("Timbre summary skipped: %s", error)
        return False
    target.write_bytes(cache.read_bytes())
    return True
