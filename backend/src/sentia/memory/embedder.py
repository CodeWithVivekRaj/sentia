"""Ollama-backed embedding generator."""
import logging
import httpx
from typing import Optional

log = logging.getLogger("sentia.memory.embedder")

EMBEDDING_DIM = 2048  # llama3.2:3b produces 3072; nomic-embed-text 768 — we detect at runtime


class Embedder:
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(timeout=30.0)
        self._dim: Optional[int] = None

    async def embed(self, text: str) -> list[float]:
        """Return embedding vector for text. Returns empty list if Ollama unreachable."""
        try:
            r = await self._client.post(
                f"{self._base_url}/api/embeddings",
                json={"model": self._model, "prompt": text},
            )
            r.raise_for_status()
            vec = r.json().get("embedding", [])
            if vec and self._dim is None:
                self._dim = len(vec)
                log.info("Embedding dim detected: %d (model=%s)", self._dim, self._model)
            return vec
        except Exception:
            log.debug("Embedding failed — Ollama unreachable or model unsupported")
            return []

    @property
    def dim(self) -> Optional[int]:
        return self._dim

    async def close(self) -> None:
        await self._client.aclose()
