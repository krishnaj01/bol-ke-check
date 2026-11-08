import json
import re

import openai

from app.config import get_settings
from app.gnani import GnaniError, LLMUnavailable, mock

MAX_OUTPUT_TOKENS = 1500
THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def make_client() -> openai.AsyncOpenAI:
    settings = get_settings()
    return openai.AsyncOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key or "not-required",
        timeout=settings.llm_timeout_sec,
        max_retries=1,
    )


def parse_json_reply(content: str) -> dict:
    match = JSON_OBJECT.search(THINK_BLOCK.sub("", content))
    if match is None:
        raise ValueError("Reply contained no JSON object")
    return json.loads(match.group())


async def chat(messages: list[dict], json_schema: dict) -> dict:
    settings = get_settings()
    if settings.gnani_mock:
        return mock.chat(messages, json_schema)
    if not settings.llm_base_url:
        raise LLMUnavailable("LLM_BASE_URL is not set")
    try:
        completion = await make_client().chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0,
            max_tokens=MAX_OUTPUT_TOKENS,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "review", "schema": json_schema},
            },
            # Evon spends output tokens on a reasoning trace unless disabled: vLLM reads the
            # template kwarg, Ollama reads reasoning_effort.
            extra_body={
                "chat_template_kwargs": {"enable_thinking": False},
                "reasoning_effort": "none",
            },
        )
    except openai.OpenAIError as error:
        raise GnaniError(f"LLM call failed: {type(error).__name__}") from error
    return parse_json_reply(completion.choices[0].message.content or "")
