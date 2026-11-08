import json
import logging
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from app import rules_engine
from app.config import BACKEND_ROOT, get_settings
from app.gnani import GnaniError, llm
from app.models import Flag, Segment, Severity
from app.rules_engine import FAMILIES, fold_token

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH: Path = BACKEND_ROOT / "prompts" / "review.md"
EXAMPLES_PATH: Path = BACKEND_ROOT / "prompts" / "review_examples.json"
INSTRUCTIONS = (
    "Return new flags under 'flags'. Also return one safer line under 'rewrites' "
    "for each ALREADY_FLAGGED item, using its id as flag_id.\n"
)
MAX_WORDS_PER_CHUNK = 3000
QUOTE_MATCH_MIN = 0.8
MIN_MATCH_RUN = 3
REWRITE_FALLBACK = "Rephrase this as your own experience, without promising an outcome."


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


def _example_turns() -> list[dict]:
    turns: list[dict] = []
    for example in json.loads(EXAMPLES_PATH.read_text(encoding="utf-8")):
        turns.append(
            {
                "role": "user",
                "content": INSTRUCTIONS + json.dumps(example["input"], ensure_ascii=False),
            }
        )
        turns.append(
            {"role": "assistant", "content": json.dumps(example["output"], ensure_ascii=False)}
        )
    return turns


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
    return [
        {"role": "system", "content": SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")},
        *_example_turns(),
        {"role": "user", "content": INSTRUCTIONS + json.dumps(payload, ensure_ascii=False)},
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


def _fold(text: str) -> str:
    return " ".join(fold_token(token) for token in unicodedata.normalize("NFC", text).split())


def _ground_quote(quote: str, segment: Segment) -> str | None:
    """Return text that was really spoken, or None if the quote is not from this segment.

    Evon sometimes re-scripts or garbles a quote, so compare in the folded Roman view and show the
    transcript's own line rather than Evon's spelling.
    """
    if not quote.strip():
        return None
    if _squash(quote) in _squash(segment.text):
        return quote
    folded = _fold(quote)
    blocks = SequenceMatcher(None, folded, _fold(segment.text), autojunk=False).get_matching_blocks()
    matched = sum(block.size for block in blocks if block.size >= MIN_MATCH_RUN)
    if folded and matched / len(folded) >= QUOTE_MATCH_MIN:
        return segment.text.strip().rstrip("।.!?")
    return None


def _is_safe_rewrite(text: str, category: str) -> bool:
    if not text.strip():
        return False
    probe = Segment(id="probe", start_sec=0, end_sec=1, text=text)
    return not rules_engine.scan([probe], category, False, 1.0).flags


def _accept(flag: EvonFlag, quote: str, segment: Segment, rule_flags: list[Flag]) -> bool:
    if flag.family not in FAMILIES or flag.confidence < get_settings().llm_min_confidence:
        return False
    quote = _squash(quote)
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
                if rewrite.flag_id in rule_by_id and _is_safe_rewrite(
                    rewrite.suggested_rewrite, category
                ):
                    rule_by_id[rewrite.flag_id].suggested_rewrite = rewrite.suggested_rewrite
            for candidate in reply.flags:
                segment = by_id.get(candidate.segment_id)
                quote = _ground_quote(candidate.quote, segment) if segment else None
                if quote is None or not _accept(candidate, quote, segment, rule_flags):
                    continue
                rewrite = candidate.suggested_rewrite
                if not _is_safe_rewrite(rewrite, category):
                    rewrite = REWRITE_FALLBACK
                grounded = candidate.model_copy(update={"quote": quote, "suggested_rewrite": rewrite})
                flags.append(_to_flag(grounded, segment, f"f{len(flags) + 1}"))
    except (GnaniError, ValidationError, ValueError) as error:
        logger.warning("Evon layer unavailable, using rule results only: %s", error)
        return ReviewOutcome(flags=[flag.model_copy() for flag in rule_flags], partial=True)
    return ReviewOutcome(flags=flags, partial=False)
