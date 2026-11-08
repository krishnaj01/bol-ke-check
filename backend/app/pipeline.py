import json
import logging

from sqlmodel import Session

from app.db import engine
from app.gnani import mock
from app.models import Check, Disclosure, Report, Segment

logger = logging.getLogger(__name__)


def _update(check_id: str, **fields) -> None:
    with Session(engine) as session:
        check = session.get(Check, check_id)
        for key, value in fields.items():
            setattr(check, key, value)
        session.add(check)
        session.commit()


async def run_check(check_id: str) -> None:
    with Session(engine) as session:
        check = session.get(Check, check_id)
        category, paid_collab, source = check.category, check.paid_collab, check.source_name

    segments = [
        Segment(
            id=f"s{i + 1}",
            start_sec=i * 5.0,
            end_sec=(i + 1) * 5.0,
            text=mock.transcribe(b"", "hi-IN", script=source, index=i)["text"],
        )
        for i in range(4)
    ]
    report = Report(
        check_id=check_id,
        category=category,
        risk_score=0,
        risk_level="low",
        duration_sec=20.0,
        disclosure=Disclosure(required=paid_collab, found=False),
        segments=segments,
        status="complete",
        stage="done",
    )
    _update(
        check_id,
        status="complete",
        stage="done",
        duration_sec=20.0,
        risk_score=0,
        risk_level="low",
        report_json=json.dumps(report.model_dump()),
    )
