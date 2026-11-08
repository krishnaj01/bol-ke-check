from dataclasses import dataclass, field

from app.models import Disclosure, Flag, Segment

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
