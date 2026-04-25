"""Ollama adapter - calls local Ollama HTTP API."""
import time
import httpx
from typing import AsyncIterator
from .interface import LLMInterface, LLMRequest, LLMResponse


class OllamaAdapter(LLMInterface):
    def __init__(self, base_url: str, model: str):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(timeout=120.0)

    @property
    def model(self) -> str:
        return self._model

    def set_model(self, model: str) -> None:
        self._model = model

    async def generate(self, request: LLMRequest) -> LLMResponse:
        start = time.monotonic()
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        resp = await self._client.post(
            f"{self._base_url}/api/chat",
            json={
                "model": self._model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens,
                },
            },
        )
        resp.raise_for_status()
        data = resp.json()
        duration_ms = (time.monotonic() - start) * 1000

        content = data.get("message", {}).get("content", "")
        tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

        return LLMResponse(
            content=content,
            model=self._model,
            tokens_used=tokens,
            duration_ms=duration_ms,
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})

        async with self._client.stream(
            "POST",
            f"{self._base_url}/api/chat",
            json={
                "model": self._model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": request.temperature},
            },
        ) as response:
            response.raise_for_status()
            import json
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

    async def is_available(self) -> bool:
        try:
            resp = await self._client.get(f"{self._base_url}/api/version", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
