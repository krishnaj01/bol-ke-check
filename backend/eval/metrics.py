from dataclasses import dataclass
from statistics import median

from app.models import Disclosure, Flag

TOLERANCE_SEC = 3.0
LATENCY_CLIP_RANGE_SEC = (45.0, 75.0)
DISCLOSURE_FAMILY = "missing_disclosure"


@dataclass
class Violation:
    family: str
    time_sec: float | None = None


@dataclass
class ClipResult:
    clip_id: str
    paid_collab: bool
    disclosed: bool
    violations: list[Violation]
    flags: list[Flag]
    disclosure: Disclosure | None
    duration_sec: float
    latency_sec: float
    status: str


def _matches(flag: Flag, violation: Violation) -> bool:
    if flag.family != violation.family:
        return False
    if violation.time_sec is None:
        return True
    return flag.start_sec - TOLERANCE_SEC <= violation.time_sec <= flag.end_sec + TOLERANCE_SEC


def compute_metrics(results: list[ClipResult]) -> dict:
    planted = caught = false_alarms = rule_catches = llm_catches = 0
    disclosure_correct = disclosure_total = 0
    for result in results:
        planted += len(result.violations)
        for violation in result.violations:
            hits = [flag for flag in result.flags if _matches(flag, violation)]
            if hits:
                caught += 1
                if any(flag.layer == "rule" for flag in hits):
                    rule_catches += 1
                else:
                    llm_catches += 1
        false_alarms += sum(
            not any(_matches(flag, violation) for violation in result.violations)
            for flag in result.flags
        )
        if result.paid_collab and result.disclosure is not None:
            disclosure_total += 1
            disclosure_correct += result.disclosure.found == result.disclosed

    latencies = [
        result.latency_sec
        for result in results
        if LATENCY_CLIP_RANGE_SEC[0] <= result.duration_sec <= LATENCY_CLIP_RANGE_SEC[1]
    ]
    clips = len(results)
    return {
        "clips": clips,
        "planted": planted,
        "caught": caught,
        "recall": caught / planted if planted else 0.0,
        "false_alarms": false_alarms,
        "false_alarms_per_clip": false_alarms / clips if clips else 0.0,
        "disclosure_accuracy": (
            disclosure_correct / disclosure_total if disclosure_total else None
        ),
        "layer_split": {"rule": rule_catches, "llm": llm_catches},
        "median_latency_sec": median(latencies) if latencies else None,
        "partial_clips": sum(result.status == "partial" for result in results),
        "failed_clips": sum(result.status == "failed" for result in results),
    }
