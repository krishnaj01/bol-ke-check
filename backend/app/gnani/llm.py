from app.config import get_settings
from app.gnani import LLMUnavailable, mock


async def chat(messages: list[dict], json_schema: dict) -> dict:
    if get_settings().gnani_mock:
        return mock.chat(messages, json_schema)
    raise LLMUnavailable("LLM client not configured")
