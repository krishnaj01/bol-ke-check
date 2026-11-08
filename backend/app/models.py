from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import Field as PydanticField
from sqlmodel import Field, SQLModel

Severity = Literal["high", "medium", "low"]
Layer = Literal["rule", "llm"]
RiskLevel = Literal["low", "medium", "high"]
Status = Literal["queued", "transcribing", "reviewing", "complete", "partial", "failed"]
Stage = Literal["queued", "extract", "transcribe", "rules", "review", "summary", "done"]
ErrorCode = Literal["no_speech", "too_long", "bad_media", "gnani_failed", "internal"]

CATEGORIES = ("personal_care", "food", "finance", "health", "betting", "general")
TERMINAL_STATUSES = ("complete", "partial", "failed")
DISCLAIMER = "Automated pre-check, not legal advice."


def utcnow() -> datetime:
    return datetime.now(UTC)


class Check(SQLModel, table=True):
    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    category: str
    paid_collab: bool = False
    brand: str | None = None
    speak_summary: bool = False
    source_name: str = ""
    input_file: str = ""
    status: str = "queued"
    stage: str = "queued"
    duration_sec: float | None = None
    risk_score: int | None = None
    risk_level: str | None = None
    report_json: str | None = None
    error: str | None = None


class TranscriptCache(SQLModel, table=True):
    audio_sha256: str = Field(primary_key=True)
    language: str = Field(primary_key=True)
    text: str
    provider_raw_json: str


class EvalRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    dataset_version: str
    metrics_json: str


class UsageCounter(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    stt_seconds: float = 0.0


class Segment(BaseModel):
    id: str
    start_sec: float
    end_sec: float
    text: str


class Flag(BaseModel):
    id: str
    rule_id: str
    family: str
    title: str
    layer: Layer
    severity: Severity
    start_sec: float
    end_sec: float
    quote: str
    explanation: str
    suggested_rewrite: str
    confidence: float = PydanticField(ge=0, le=1)
    verified: bool = False
    source: str | None = None


class Disclosure(BaseModel):
    required: bool
    found: bool
    first_at_sec: float | None = None


class Report(BaseModel):
    check_id: str
    category: str
    risk_score: int | None = None
    risk_level: RiskLevel | None = None
    duration_sec: float | None = None
    disclosure: Disclosure | None = None
    flags: list[Flag] = []
    segments: list[Segment] = []
    summary_hi: str | None = None
    summary_audio_url: str | None = None
    media_url: str | None = None
    disclaimer: str = DISCLAIMER
    status: Status
    stage: Stage = "queued"
    error: ErrorCode | None = None
