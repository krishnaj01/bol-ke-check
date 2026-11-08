import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import audio, review, scoring, summary
from app.gnani import llm
from app.models import Disclosure, Flag, Segment
from scripts.speechlike import speech_like_pcm, write_wav


def make_flag(layer="rule", severity="high", confidence=1.0, flag_id="f1", start=1.0) -> Flag:
    return Flag(
        id=flag_id, rule_id="R1", family="guaranteed_results", title="T", layer=layer,
        severity=severity, start_sec=start, end_sec=start + 3, quote="pakka glow",
        explanation="e", suggested_rewrite="fix", confidence=confidence,
    )


@pytest.fixture
def speech_wav(tmp_path: Path) -> Path:
    path = tmp_path / "speech.wav"
    write_wav(path, speech_like_pcm([5.0, 5.0, 5.0, 5.0], gap=0.8))
    return path


def test_extract_writes_16k_mono_and_pcm_length_matches(speech_wav: Path, tmp_path: Path) -> None:
    target = tmp_path / "out.wav"
    audio.extract_wav(speech_wav, target)
    assert audio.duration_of(audio.read_pcm(target)) == pytest.approx(24.0, abs=0.2)


def test_extract_rejects_non_media(tmp_path: Path) -> None:
    bad = tmp_path / "bad.mp4"
    bad.write_bytes(b"not media")
    with pytest.raises(audio.MediaError):
        audio.extract_wav(bad, tmp_path / "out.wav")


def test_vad_finds_one_segment_per_burst(speech_wav: Path) -> None:
    spans = audio.speech_segments(audio.read_pcm(speech_wav))
    assert len(spans) == 4
    assert all(3.0 <= end - start <= audio.MAX_SEGMENT_SEC + 1 for start, end in spans)


def test_silence_has_no_segments() -> None:
    assert audio.speech_segments(b"\x00" * 16000 * 2 * 3) == []


def test_merge_joins_short_neighbours_and_respects_max() -> None:
    assert audio.merge_regions([(0.0, 1.0), (1.5, 4.0)]) == [(0.0, 4.0)]
    assert audio.merge_regions([(0.0, 8.0), (8.1, 14.0)]) == [(0.0, 8.0), (8.1, 14.0)]


def test_split_long_keeps_every_piece_under_max() -> None:
    pieces = audio.split_long([(0.0, 30.0)])
    assert len(pieces) == 3
    assert all(end - start <= audio.MAX_SEGMENT_SEC for start, end in pieces)


def test_score_weights_and_llm_confidence() -> None:
    flags = [make_flag(), make_flag(layer="llm", severity="medium", confidence=0.8)]
    assert scoring.risk_score(flags) == 47


def test_score_caps_at_100_and_levels() -> None:
    assert scoring.risk_score([make_flag()] * 4) == 100
    assert [scoring.risk_level(s) for s in (24, 25, 59, 60)] == [
        "low", "medium", "medium", "high",
    ]


def test_summary_counts_flags_and_mentions_missing_disclosure() -> None:
    text = summary.build_display(
        [make_flag(start=14.0)], 35, "medium", Disclosure(required=True, found=False)
    )
    assert "1 jagah risk" in text and "0:14" in text and "Paid partnership" in text


def test_spoken_summary_is_devanagari() -> None:
    text = summary.build_spoken([make_flag()], 60, "high", Disclosure(required=False, found=False))
    assert "1 जगह रिस्क" in text and "100 में से 60" in text


SEGMENTS = [Segment(id="s1", start_sec=0.0, end_sec=4.0, text="ye bilkul safe hai doston")]


def _patch_families(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(review, "FAMILIES", {"unqualified_advice": "d", "guaranteed_results": "d"})


def _evon_flag(**overrides) -> dict:
    return {
        "segment_id": "s1", "family": "unqualified_advice", "severity": "medium",
        "quote": "bilkul safe hai", "explanation": "e", "suggested_rewrite": "r",
        "confidence": 0.8, **overrides,
    }


def _run_review(monkeypatch: pytest.MonkeyPatch, replies: list, rule_flags=None):
    _patch_families(monkeypatch)
    calls: list[list[dict]] = []

    async def fake_chat(messages: list[dict], schema: dict) -> dict:
        calls.append(messages)
        reply = replies[len(calls) - 1]
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr(llm, "chat", fake_chat)
    outcome = asyncio.run(review.review_transcript(SEGMENTS, "health", None, rule_flags or []))
    return outcome, calls


def test_review_accepts_real_quote(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome, _ = _run_review(monkeypatch, [{"flags": [_evon_flag()]}])
    assert not outcome.partial
    assert [flag.layer for flag in outcome.flags] == ["llm"]
    assert outcome.flags[0].start_sec == 0.0


@pytest.mark.parametrize(
    "bad",
    [
        {"quote": "ye quote kabhi bola nahi gaya"},
        {"family": "invented_family"},
        {"confidence": 0.2},
        {"segment_id": "s99"},
    ],
)
def test_review_drops_unsupported_flags(monkeypatch: pytest.MonkeyPatch, bad: dict) -> None:
    outcome, _ = _run_review(monkeypatch, [{"flags": [_evon_flag(**bad)]}])
    assert outcome.flags == [] and not outcome.partial


def test_review_retries_once_with_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome, calls = _run_review(monkeypatch, [{"flags": "nope"}, {"flags": [_evon_flag()]}])
    assert len(calls) == 2 and "failed validation" in calls[1][-1]["content"]
    assert len(outcome.flags) == 1 and not outcome.partial


def test_review_falls_back_to_partial_after_second_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    rule_flag = make_flag(start=0.0)
    outcome, calls = _run_review(monkeypatch, [{"flags": "x"}, {"flags": "y"}], [rule_flag])
    assert len(calls) == 2 and outcome.partial
    assert [flag.id for flag in outcome.flags] == ["f1"]


def test_review_applies_rewrites_to_rule_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    reply = {"rewrites": [{"flag_id": "f1", "suggested_rewrite": "naya line"}]}
    outcome, _ = _run_review(monkeypatch, [reply], [make_flag(start=0.0)])
    assert outcome.flags[0].suggested_rewrite == "naya line"


def test_review_does_not_repeat_rule_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    duplicate = _evon_flag(family="guaranteed_results")
    outcome, _ = _run_review(monkeypatch, [{"flags": [duplicate]}], [make_flag(start=0.0)])
    assert len(outcome.flags) == 1 and outcome.flags[0].layer == "rule"


def test_chunking_splits_long_transcripts() -> None:
    long = [Segment(id=f"s{i}", start_sec=i, end_sec=i + 1, text="word " * 2000) for i in range(3)]
    assert [len(chunk) for chunk in review.chunk_segments(long)] == [1, 1, 1]


def test_flag_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        make_flag(confidence=1.5)


def _upload(client: TestClient, wav: Path, name: str, **form) -> dict:
    response = client.post(
        "/api/v1/check",
        files={"file": (name, wav.read_bytes(), "audio/wav")},
        data={"category": "personal_care", **form},
    )
    assert response.status_code == 202, response.text
    return client.get(f"/api/v1/check/{response.json()['check_id']}").json()


def test_full_pipeline_with_mock(client: TestClient, speech_wav: Path) -> None:
    report = _upload(client, speech_wav, "sample_no_disclosure.wav", speak_summary="true")
    assert report["status"] == "complete"
    assert len(report["segments"]) == 4
    assert report["segments"][0]["start_sec"] < report["segments"][1]["start_sec"]
    assert any(flag["layer"] == "llm" for flag in report["flags"])
    audio_response = client.get(report["summary_audio_url"])
    assert audio_response.status_code == 200 and len(audio_response.content) > 100
    media = client.get(report["media_url"], headers={"Range": "bytes=0-99"})
    assert media.status_code == 206


def test_silent_upload_fails_with_no_speech(client: TestClient, tmp_path: Path) -> None:
    silent = tmp_path / "silent.wav"
    write_wav(silent, b"\x00" * 16000 * 2 * 3)
    report = _upload(client, silent, "silent.wav")
    assert (report["status"], report["error"]) == ("failed", "no_speech")


def test_garbage_upload_fails_with_bad_media(client: TestClient, tmp_path: Path) -> None:
    garbage = tmp_path / "g.mp4"
    garbage.write_bytes(b"not actually a video")
    report = _upload(client, garbage, "g.mp4")
    assert (report["status"], report["error"]) == ("failed", "bad_media")


def test_retry_requires_failed_check(client: TestClient, speech_wav: Path, tmp_path: Path) -> None:
    done = _upload(client, speech_wav, "a.wav")
    assert client.post(f"/api/v1/check/{done['check_id']}/retry").status_code == 409

    silent = tmp_path / "silent.wav"
    write_wav(silent, b"\x00" * 16000 * 2 * 3)
    failed = _upload(client, silent, "s.wav")
    assert client.post(f"/api/v1/check/{failed['check_id']}/retry").status_code == 202
