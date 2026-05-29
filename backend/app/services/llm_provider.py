from collections.abc import AsyncIterator
from typing import Protocol

from openai import AsyncOpenAI

from app.core.config import Settings


class LLMProvider(Protocol):
    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]: ...


class OpenAICompatibleLLMProvider:
    def __init__(self, settings: Settings):
        settings.validate_llm_config()
        kwargs = {
            "api_key": (
                settings.LLM_API_KEY.get_secret_value()
                if settings.LLM_API_KEY
                else ""
            )
        }
        if settings.LLM_BASE_URL:
            kwargs["base_url"] = settings.LLM_BASE_URL
        self.client = AsyncOpenAI(**kwargs)
        self.model = settings.LLM_MODEL

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            token = chunk.choices[0].delta.content if chunk.choices else None
            if token:
                yield token


class FakeLLMProvider:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens

    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        for token in self.tokens:
            yield token
