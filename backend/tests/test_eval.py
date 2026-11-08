import asyncio
import json
from pathlib import Path

import pytest

from app.models import Disclosure, Flag
from eval import run_eval
from eval.metrics import ClipResult, Violation, compute_metrics


def flag(family: str, start: float, end: float, layer: str = "rule") -> Flag:
    return Flag(
        id="f", rule_id="R", family=family, title="T", layer=layer, severity="high",
        start_sec=start, end_sec=end, quote="q", explanation="e",
        suggested_rewrite="r", confidence=0.9,
    )


def clip(violations=(), flags=(), paid=False, disclosed=False, found=False, duration=30.0):
    return ClipResult(
        clip_id="c", paid_collab=paid, disclosed=disclosed, violations=list(violations),
        flags=list(flags), disclosure=Disclosure(required=paid, found=found),
        duration_sec=duration, latency_sec=12.0, status="complete",
    )


def test_catch_needs_family_and_three_second_window() -> None:
    planted = [Violation("guaranteed_results", 20.0)]
    assert compute_metrics([clip(planted, [flag("guaranteed_results", 22.0, 25.0)])])["caught"] == 1
    assert compute_metrics([clip(planted, [flag("guaranteed_results", 24.0, 26.0)])])["caught"] == 0
    assert compute_metrics([clip(planted, [flag("superlatives", 19.0, 21.0)])])["caught"] == 0


def test_unmatched_flag_is_false_alarm() -> None:
    metrics = compute_metrics([clip([], [flag("superlatives", 1.0, 2.0)])])
    assert metrics["false_alarms"] == 1 and metrics["false_alarms_per_clip"] == 1.0


def test_second_layer_on_same_violation_is_not_a_false_alarm() -> None:
    planted = [Violation("guaranteed_results", 5.0)]
    flags = [flag("guaranteed_results", 4.0, 6.0), flag("guaranteed_results", 4.0, 6.0, "llm")]
    metrics = compute_metrics([clip(planted, flags)])
    assert (metrics["caught"], metrics["false_alarms"]) == (1, 0)
    assert metrics["layer_split"] == {"rule": 1, "llm": 0}


def test_layer_split_credits_evon_only_catch() -> None:
    planted = [Violation("unqualified_advice", 5.0)]
    metrics = compute_metrics([clip(planted, [flag("unqualified_advice", 4.0, 6.0, "llm")])])
    assert metrics["layer_split"] == {"rule": 0, "llm": 1}


def test_disclosure_accuracy_only_counts_paid_clips() -> None:
    results = [
        clip(paid=True, disclosed=True, found=True),
        clip(paid=True, disclosed=True, found=False),
        clip(paid=False, disclosed=False, found=True),
    ]
    assert compute_metrics(results)["disclosure_accuracy"] == 0.5


def test_latency_uses_only_about_sixty_second_clips() -> None:
    assert compute_metrics([clip(duration=20.0)])["median_latency_sec"] is None
    assert compute_metrics([clip(duration=60.0)])["median_latency_sec"] == 12.0


def test_empty_results_do_not_divide_by_zero() -> None:
    metrics = compute_metrics([])
    assert metrics["recall"] == 0.0 and metrics["disclosure_accuracy"] is None


def test_real_run_refuses_mock_mode() -> None:
    assert asyncio.run(run_eval.main("test", dry_run=False)) == 2


def test_dry_run_is_not_published(
    client, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from app.config import get_settings

    monkeypatch.setattr(run_eval, "OUTPUT", tmp_path)
    assert asyncio.run(run_eval.main("dev", dry_run=True)) == 0
    metrics = json.loads((tmp_path / "metrics.json").read_text())
    assert metrics["mode"] == "mock" and metrics["clips"] == 10
    assert not (get_settings().media_dir / "eval" / "metrics.json").exists()


def test_mock_speech_never_enters_the_real_cache(client) -> None:
    from app import summary
    from app.config import get_settings

    asyncio.run(summary.cached_speech("नमस्ते", "Nalini"))
    assert not (get_settings().media_dir / "_tts_cache").exists()
