from app.models import Flag, RiskLevel

SEVERITY_POINTS = {"high": 35, "medium": 15, "low": 5}
MEDIUM_FROM = 25
HIGH_FROM = 60


def risk_level(score: int) -> RiskLevel:
    if score >= HIGH_FROM:
        return "high"
    return "medium" if score >= MEDIUM_FROM else "low"


def risk_score(flags: list[Flag]) -> int:
    total = sum(
        SEVERITY_POINTS[flag.severity] * (flag.confidence if flag.layer == "llm" else 1)
        for flag in flags
    )
    return min(100, round(total))
