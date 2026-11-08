import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="bolkecheck-test-"))
os.environ.update(
    GNANI_MOCK="1",
    DATABASE_URL=f"sqlite:///{_tmp}/test.db",
    MEDIA_DIR=str(_tmp / "media"),
    CREDIT_GUARD_SECONDS="0",
    LLM_BASE_URL="",
)

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
