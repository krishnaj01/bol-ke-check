import logging

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings
from app.gnani import GnaniError

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
TIMEOUT_SEC = 60.0


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=TIMEOUT_SEC)


def _should_retry(error: BaseException) -> bool:
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in RETRYABLE_STATUS
    return isinstance(error, httpx.TransportError)


@retry(
    retry=retry_if_exception(_should_retry),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=4),
    reraise=True,
)
async def _post(url: str, headers: dict, **kwargs) -> httpx.Response:
    async with make_client() as client:
        response = await client.post(url, headers=headers, **kwargs)
    response.raise_for_status()
    return response


async def post_gnani(url: str, **kwargs) -> httpx.Response:
    api_key = get_settings().gnani_api_key
    if not url or not api_key:
        raise GnaniError("Gnani URL or API key is not configured")
    try:
        return await _post(url, {"X-API-Key-ID": api_key}, **kwargs)
    except httpx.HTTPStatusError as error:
        status = error.response.status_code
        logger.warning("Gnani returned %s: %s", status, error.response.text[:300])
        raise GnaniError(f"Gnani returned HTTP {status}") from error
    except httpx.TransportError as error:
        raise GnaniError(f"Could not reach Gnani: {type(error).__name__}") from error
