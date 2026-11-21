"""Optional LLM generation on top of local retrieval.

Retrieval always runs locally and is mandatory. Generation is optional: with
the default ``deterministic`` provider the reviewed answer catalogue is used
unchanged, so the platform works offline and without an API key. When a model
provider is configured, it receives only retrieved passages and falls back to
the deterministic answer on any error, timeout or unsafe output.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping

import httpx

from app.core.config import Settings, get_settings
from app.services.rag.guardrails import (
    build_context,
    contains_prompt_injection,
    sanitize_answer,
    system_prompt,
)


@dataclass(frozen=True)
class GenerationResult:
    """The outcome of an attempted generation, including any failover."""

    text: str | None
    provider: str
    used: bool
    failover_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "used": self.used,
            "failover_reason": self.failover_reason,
        }


class BaseProvider(ABC):
    """A generator that turns retrieved context into an answer."""

    name = "base"

    @abstractmethod
    async def generate(
        self,
        *,
        query: str,
        context: str,
        language: str,
        settings: Settings,
    ) -> str | None:
        """Return an answer, or ``None`` to keep the reviewed response."""


class DeterministicProvider(BaseProvider):
    """No model call: the reviewed answer and citations are already enough."""

    name = "deterministic"

    async def generate(self, **_: Any) -> str | None:
        return None


class OllamaProvider(BaseProvider):
    """A local Ollama model, reached over the already-installed ``httpx``."""

    name = "ollama"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def generate(
        self,
        *,
        query: str,
        context: str,
        language: str,
        settings: Settings,
    ) -> str | None:
        payload = {
            "model": settings.ai_ollama_model,
            "prompt": f"{system_prompt(language)}\n\nCONTEXT:\n{context}\n\nQUESTION: {query}\n\nANSWER:",
            "stream": False,
            "options": {"temperature": 0.1},
        }
        response = await self._post(settings.ai_ollama_url, payload, settings)
        data = response.json()
        if not isinstance(data, dict):
            return None
        return str(data.get("response") or "")

    async def _post(
        self, url: str, payload: dict[str, Any], settings: Settings
    ) -> httpx.Response:
        if self._client is not None:
            return await self._client.post(url, json=payload)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.ai_timeout_seconds)
        ) as client:
            return await client.post(url, json=payload)


class GeminiProvider(BaseProvider):
    """Google's free-tier Gemini API. The key is injected via ``AI_GEMINI_API_KEY``."""

    name = "gemini"

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def generate(
        self,
        *,
        query: str,
        context: str,
        language: str,
        settings: Settings,
    ) -> str | None:
        if not settings.ai_gemini_api_key:
            return None
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.ai_gemini_model}:generateContent"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt(language)}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"CONTEXT:\n{context}\n\nQUESTION: {query}"
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {"temperature": 0.1},
        }
        response = await self._post(url, payload, settings, settings.ai_gemini_api_key)
        data = response.json()
        if not isinstance(data, dict):
            return None
        try:
            return str(
                data["candidates"][0]["content"]["parts"][0]["text"]
            )
        except (KeyError, IndexError, TypeError):
            return None

    async def _post(
        self, url: str, payload: dict[str, Any], settings: Settings, key: str
    ) -> httpx.Response:
        if self._client is not None:
            return await self._client.post(url, params={"key": key}, json=payload)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(settings.ai_timeout_seconds)
        ) as client:
            return await client.post(url, params={"key": key}, json=payload)


def get_provider(settings: Settings | None = None) -> BaseProvider:
    """Build the configured provider. Unknown values are rejected by Settings."""
    config = settings or get_settings()
    if config.ai_provider == "ollama":
        return OllamaProvider()
    if config.ai_provider == "gemini":
        return GeminiProvider()
    return DeterministicProvider()


async def generate_grounded_answer(
    *,
    query: str,
    chunks: list[Mapping[str, Any]],
    language: str,
    settings: Settings | None = None,
    provider: BaseProvider | None = None,
) -> GenerationResult:
    """Generate from retrieved passages, failing closed to the reviewed answer."""
    config = settings or get_settings()
    generator = provider or get_provider(config)

    if contains_prompt_injection(query):
        return GenerationResult(None, "deterministic", False, "prompt_injection")
    context = build_context(chunks, max_chars=config.ai_max_context_chars)
    if not context or generator.name == "deterministic":
        return GenerationResult(None, generator.name, False, "no_generation_needed")

    try:
        raw = await asyncio.wait_for(
            generator.generate(
                query=query, context=context, language=language, settings=config
            ),
            timeout=config.ai_timeout_seconds,
        )
    except Exception as exc:  # noqa: BLE001 - fail closed on any provider fault
        return GenerationResult(
            None, "deterministic", False, f"provider_error:{type(exc).__name__}"
        )

    answer = sanitize_answer(raw or "")
    if answer is None:
        return GenerationResult(None, "deterministic", False, "unsafe_or_empty_output")
    return GenerationResult(answer, generator.name, True)
