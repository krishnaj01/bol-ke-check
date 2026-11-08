from dataclasses import dataclass, field

from app.models import Disclosure, Flag, Segment

FAMILIES: dict[str, str] = {}


@dataclass
class ScanResult:
    disclosure: Disclosure
    flags: list[Flag] = field(default_factory=list)


def scan(
    segments: list[Segment], category: str, paid_collab: bool, duration_sec: float
) -> ScanResult:
    return ScanResult(disclosure=Disclosure(required=paid_collab, found=False))


def keyterms_for(category: str) -> list[str]:
    return []
