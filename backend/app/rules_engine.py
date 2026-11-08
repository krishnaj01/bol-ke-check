import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml
from indic_transliteration import sanscript
from pydantic import BaseModel

from app.config import BACKEND_ROOT
from app.models import CATEGORIES, Disclosure, Flag, Segment, Severity

RULES_DIR: Path = BACKEND_ROOT / "rules"

FAMILIES: dict[str, str] = {
    "missing_disclosure": "A paid collaboration that is not disclosed in the spoken audio.",
    "guaranteed_results": "Guaranteed, instant or time-bound outcome claims.",
    "assured_returns": "Assured investment returns or claims of no financial risk.",
    "unqualified_advice": "Financial, medical or expert advice or endorsement without credentials.",
    "disease_cure": "Claims that a product cures or treats a disease.",
    "betting_promotion": "Promoting betting or gambling, or promising winnings.",
    "superlatives": "Number-one or best-in-class claims without proof.",
    "fake_urgency": "Pressure to act now without a real, stated end date.",
}

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
VOWELS = "aAiIuUeEoO"
MEDIAL_SCHWA = re.compile(rf"([{VOWELS}][^{VOWELS}\s])a([^{VOWELS}\s][{VOWELS}])")
FINAL_SCHWA = re.compile(rf"(?<=[^{VOWELS}])a$")
NUKTA_EXCEPT_ZA = re.compile("(?<!ज)़")
# \w excludes Devanagari vowel signs, so the block is listed explicitly.
NON_WORD = re.compile(r"[^\w%\u0900-\u097F]+")


def _fold_vowels(text: str) -> str:
    return text.replace("aa", "a").replace("ee", "i").replace("oo", "u")


def _romanise_devanagari(token: str) -> str:
    token = NUKTA_EXCEPT_ZA.sub("", token).replace("ऑ", "ओ").replace("ॉ", "ो")
    roman = sanscript.transliterate(token, sanscript.DEVANAGARI, sanscript.ITRANS)
    roman = re.sub(r"M(?=[pbm])", "m", roman)
    roman = re.sub(r"eM$", "ein", roman).replace("M", "n").replace("~", "")
    roman = MEDIAL_SCHWA.sub(r"\1\2", FINAL_SCHWA.sub("", roman))
    return roman.replace("ph", "f")


def fold_token(token: str) -> str:
    """Reduce a Roman or Devanagari word to the one spelling that patterns are written against."""
    token = unicodedata.normalize("NFC", token)
    if DEVANAGARI.search(token):
        token = _romanise_devanagari(token)
    return _fold_vowels(NON_WORD.sub(" ", token.lower()).strip())


@dataclass(frozen=True)
class View:
    text: str
    owners: tuple[int, ...]


@dataclass(frozen=True)
class NormalisedText:
    original: str
    spans: tuple[tuple[int, int], ...]
    raw: View
    roman: View

    def quote(self, view: View, start: int, end: int) -> str:
        first = view.owners[start]
        last = view.owners[max(start, end - 1)]
        return self.original[self.spans[first][0] : self.spans[last][1]].rstrip(",.!?।")


def _build_view(parts: list[str]) -> View:
    text: list[str] = []
    owners: list[int] = []
    for index, part in enumerate(parts):
        if not part:
            continue
        if text:
            text.append(" ")
            owners.append(index)
        text.append(part)
        owners.extend([index] * len(part))
    return View("".join(text), tuple(owners))


def normalise(text: str) -> NormalisedText:
    original = unicodedata.normalize("NFC", text)
    matches = list(re.finditer(r"\S+", original))
    tokens = [match.group() for match in matches]
    return NormalisedText(
        original=original,
        spans=tuple(match.span() for match in matches),
        raw=_build_view([NON_WORD.sub("", token.lower()) or token.lower() for token in tokens]),
        roman=_build_view([fold_token(token) for token in tokens]),
    )


class RuleSpec(BaseModel):
    id: str
    category: str
    family: str
    title: str
    severity: Severity
    layer: str = "rule"
    patterns: list[str] = []
    explanation: str
    suggested_fix: str
    source: str | None = None
    verified: bool = False


class DisclosureSpec(BaseModel):
    patterns: list[str]
    early_fraction: float = 0.3


class PackFile(BaseModel):
    rules: list[RuleSpec]
    disclosure: DisclosureSpec | None = None
    keyterms: list[str] = []


@dataclass(frozen=True)
class CompiledPattern:
    regex: re.Pattern[str]
    devanagari: bool


def _compile(pattern: str) -> CompiledPattern:
    if DEVANAGARI.search(pattern):
        return CompiledPattern(re.compile(unicodedata.normalize("NFC", pattern)), True)
    return CompiledPattern(re.compile(_fold_vowels(pattern.lower())), False)


def _search(pattern: CompiledPattern, text: NormalisedText) -> str | None:
    view = text.raw if pattern.devanagari else text.roman
    match = pattern.regex.search(view.text)
    if match is None or match.start() == match.end():
        return None
    return text.quote(view, match.start(), match.end())


@lru_cache
def _read_pack(name: str) -> PackFile:
    data = yaml.safe_load((RULES_DIR / f"{name}.yaml").read_text(encoding="utf-8"))
    return PackFile.model_validate(data)


def rules_for(category: str) -> list[RuleSpec]:
    pack = _read_pack(category).rules if category in CATEGORIES and category != "general" else []
    return [*_read_pack("common").rules, *pack]


@lru_cache
def _compiled_rules(category: str) -> tuple[tuple[RuleSpec, tuple[CompiledPattern, ...]], ...]:
    return tuple(
        (rule, tuple(_compile(pattern) for pattern in rule.patterns))
        for rule in rules_for(category)
    )


def disclosure_spec() -> DisclosureSpec:
    spec = _read_pack("common").disclosure
    if spec is None:
        raise ValueError("common.yaml must define a disclosure section")
    return spec


def keyterms_for(category: str) -> list[str]:
    return _read_pack("common").keyterms


def _rule_flag(rule: RuleSpec, flag_id: str, start: float, end: float, quote: str) -> Flag:
    return Flag(
        id=flag_id,
        rule_id=rule.id,
        family=rule.family,
        title=rule.title,
        layer="rule",
        severity=rule.severity,
        start_sec=start,
        end_sec=end,
        quote=quote,
        explanation=rule.explanation,
        suggested_rewrite=rule.suggested_fix,
        confidence=1.0,
        verified=rule.verified,
        source=rule.source,
    )


@dataclass
class ScanResult:
    disclosure: Disclosure
    flags: list[Flag] = field(default_factory=list)


def _first_disclosure(texts: list[tuple[Segment, NormalisedText]]) -> float | None:
    patterns = [_compile(pattern) for pattern in disclosure_spec().patterns]
    for segment, text in texts:
        if any(_search(pattern, text) for pattern in patterns):
            return segment.start_sec
    return None


def _rule_by_id(rule_id: str) -> RuleSpec:
    return next(rule for rule in _read_pack("common").rules if rule.id == rule_id)


def scan(
    segments: list[Segment], category: str, paid_collab: bool, duration_sec: float
) -> ScanResult:
    texts = [(segment, normalise(segment.text)) for segment in segments]
    flags: list[Flag] = []

    def add(rule: RuleSpec, start: float, end: float, quote: str) -> None:
        flags.append(_rule_flag(rule, f"f{len(flags) + 1}", start, end, quote))

    for rule, patterns in _compiled_rules(category):
        for segment, text in texts:
            quote = next(filter(None, (_search(pattern, text) for pattern in patterns)), None)
            if quote:
                add(rule, segment.start_sec, segment.end_sec, quote)

    first_at = _first_disclosure(texts)
    if paid_collab and first_at is None:
        add(_rule_by_id("DISC-MISSING-01"), 0.0, duration_sec, "(no spoken disclosure found)")
    elif paid_collab and first_at > disclosure_spec().early_fraction * duration_sec:
        add(_rule_by_id("DISC-LATE-01"), first_at, first_at, "(disclosure comes late)")

    return ScanResult(
        disclosure=Disclosure(
            required=paid_collab, found=first_at is not None, first_at_sec=first_at
        ),
        flags=flags,
    )
