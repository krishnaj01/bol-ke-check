from fastapi.testclient import TestClient


def _upload(client: TestClient, name: str = "sample_clean.wav", **form) -> dict:
    response = client.post(
        "/api/v1/check",
        files={"file": (name, b"RIFF0000WAVE", "audio/wav")},
        data={"category": "personal_care", **form},
    )
    assert response.status_code == 202, response.text
    return response.json()


def test_health_reports_mock(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok", "mock": True}


def test_create_returns_queued_id(client: TestClient) -> None:
    created = _upload(client)
    assert created["check_id"].startswith("chk_")
    assert created["status"] == "queued"


def test_rejects_unsupported_extension(client: TestClient) -> None:
    response = client.post("/api/v1/check", files={"file": ("x.exe", b"MZ", "text/plain")})
    assert response.status_code == 415


def test_rejects_unknown_category(client: TestClient) -> None:
    response = client.post(
        "/api/v1/check",
        files={"file": ("a.wav", b"RIFF", "audio/wav")},
        data={"category": "crypto"},
    )
    assert response.status_code == 422


def test_unknown_check_is_404(client: TestClient) -> None:
    assert client.get("/api/v1/check/chk_nope").status_code == 404


def test_report_reaches_terminal_status(client: TestClient) -> None:
    check_id = _upload(client)["check_id"]
    report = client.get(f"/api/v1/check/{check_id}").json()
    assert report["check_id"] == check_id
    assert report["status"] in ("complete", "partial", "failed")


def test_events_stream_ends_on_terminal_status(client: TestClient) -> None:
    check_id = _upload(client)["check_id"]
    with client.stream("GET", f"/api/v1/check/{check_id}/events") as stream:
        body = "".join(stream.iter_text())
    assert "event: progress" in body
