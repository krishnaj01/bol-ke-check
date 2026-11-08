import json
import logging
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from app.config import BACKEND_ROOT, get_settings
from app.gnani import GnaniError, llm
from app.models import Flag, Segment, Severity
from app.rules_engine import FAMILIES

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH: Path = BACKEND_ROOT / "prompts" / "review.md"
MAX_WORDS_PER_CHUNK = 3000


class EvonFlag(BaseModel):
    segment_id: str
    family: str
    severity: Severity
    quote: str
    explanation: str
    suggested_rewrite: str
    confidence: float = Field(ge=0, le=1)


class EvonRewrite(BaseModel):
    flag_id: str
    suggested_rewrite: str


class EvonReply(BaseModel):
    flags: list[EvonFlag] = []
    rewrites: list[EvonRewrite] = []


@dataclass
class ReviewOutcome:
    flags: list[Flag]
    partial: bool


def chunk_segments(segments: list[Segment]) -> list[list[Segment]]:
    chunks: list[list[Segment]] = [[]]
    words = 0
    for segment in segments:
        count = len(segment.text.split())
        if chunks[-1] and words + count > MAX_WORDS_PER_CHUNK:
            chunks.append([])
            words = 0
        chunks[-1].append(segment)
        words += count
    return chunks


def _build_messages(
    segments: list[Segment], category: str, brand: str | None, rule_flags: list[Flag]
) -> list[dict]:
    payload = {
        "category": category,
        "brand": brand,
        "rule_families": FAMILIES,
        "ALREADY_FLAGGED": [
            {
                "id": flag.id,
                "family": flag.family,
                "quote": flag.quote,
                "suggested_fix": flag.suggested_rewrite,
            }
            for flag in rule_flags
        ],
        "segments": [segment.model_dump() for segment in segments],
    }
    instructions = (
        "Return new flags under 'flags'. Also return one safer line under 'rewrites' "
        "for each ALREADY_FLAGGED item, using its id as flag_id.\n"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")},
        {"role": "user", "content": instructions + json.dumps(payload, ensure_ascii=False)},
    ]


async def _ask_evon(messages: list[dict]) -> EvonReply:
    schema = EvonReply.model_json_schema()
    try:
        return EvonReply.model_validate(await llm.chat(messages, schema))
    except (ValidationError, ValueError) as error:
        logger.warning("Evon reply failed validation, retrying once: %s", error)
        correction = {
            "role": "user",
            "content": f"Your reply failed validation: {error}. Return only corrected JSON.",
        }
        return EvonReply.model_validate(await llm.chat([*messages, correction], schema))


def _squash(text: str) -> str:
    return " ".join(text.split()).casefold()


def _accept(flag: EvonFlag, segment: Segment | None, rule_flags: list[Flag]) -> bool:
    if segment is None or flag.family not in FAMILIES:
        return False
    if flag.confidence < get_settings().llm_min_confidence:
        return False
    quote = _squash(flag.quote)
    if not quote or quote not in _squash(segment.text):
        return False
    return not any(
        existing.start_sec == segment.start_sec
        and (
            existing.family == flag.family
            or quote in _squash(existing.quote)
            or _squash(existing.quote) in quote
        )
        for existing in rule_flags
    )


def _to_flag(flag: EvonFlag, segment: Segment, flag_id: str) -> Flag:
    return Flag(
        id=flag_id,
        rule_id=f"EVON-{flag.family.upper()}",
        family=flag.family,
        title=flag.family.replace("_", " ").capitalize(),
        layer="llm",
        severity=flag.severity,
        start_sec=segment.start_sec,
        end_sec=segment.end_sec,
        quote=flag.quote,
        explanation=flag.explanation,
        suggested_rewrite=flag.suggested_rewrite,
        confidence=flag.confidence,
    )


async def review_transcript(
    segments: list[Segment], category: str, brand: str | None, rule_flags: list[Flag]
) -> ReviewOutcome:
    by_id = {segment.id: segment for segment in segments}
    flags = [flag.model_copy() for flag in rule_flags]
    rule_by_id = {flag.id: flag for flag in flags}
    try:
        for chunk in chunk_segments(segments):
            reply = await _ask_evon(_build_messages(chunk, category, brand, rule_flags))
            for rewrite in reply.rewrites:
                if rewrite.flag_id in rule_by_id and rewrite.suggested_rewrite.strip():
                    rule_by_id[rewrite.flag_id].suggested_rewrite = rewrite.suggested_rewrite
            for candidate in reply.flags:
                segment = by_id.get(candidate.segment_id)
                if _accept(candidate, segment, rule_flags):
                    flags.append(_to_flag(candidate, segment, f"f{len(flags) + 1}"))
    except (GnaniError, ValidationError, ValueError) as error:
        logger.warning("Evon layer unavailable, using rule results only: %s", error)
        return ReviewOutcome(flags=[flag.model_copy() for flag in rule_flags], partial=True)
    return ReviewOutcome(flags=flags, partial=False)
