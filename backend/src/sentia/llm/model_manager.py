"""Model manager - discovers, tracks, and switches Ollama models."""
import httpx
from dataclasses import dataclass
from typing import Optional
import asyncio


# Approximate VRAM requirements in GB (rough estimates)
VRAM_ESTIMATES: dict[str, float] = {
    "llama3.2:1b": 1.0,
    "llama3.2:3b": 2.5,
    "llama3.1:8b": 5.5,
    "llama3.1:70b": 48.0,
    "mistral:7b": 4.5,
    "mistral-nemo": 8.0,
    "phi3:mini": 2.0,
    "phi3:medium": 4.0,
    "gemma2:2b": 1.6,
    "gemma2:9b": 6.0,
    "qwen2.5:3b": 2.5,
    "qwen2.5:7b": 4.5,
    "deepseek-r1:7b": 4.5,
    "tinyllama": 0.8,
    "orca-mini": 2.0,
    "neural-chat": 4.5,
}

AVAILABLE_VRAM_GB = 6.0  # RTX 2060


@dataclass
class ModelInfo:
    name: str
    size_gb: float
    vram_estimate_gb: float
    fits_in_vram: bool
    is_installed: bool = True
    digest: str = ""


class ModelManager:
    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=30.0)
        self._current_model: Optional[str] = None
        self._models_cache: list[ModelInfo] = []

    async def list_models(self) -> list[ModelInfo]:
        try:
            resp = await self._client.get(f"{self._base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = []
            for m in data.get("models", []):
                name = m.get("name", "")
                size_bytes = m.get("size", 0)
                size_gb = size_bytes / (1024 ** 3)
                vram_est = self._estimate_vram(name, size_gb)
                models.append(ModelInfo(
                    name=name,
                    size_gb=round(size_gb, 2),
                    vram_estimate_gb=round(vram_est, 2),
                    fits_in_vram=vram_est <= AVAILABLE_VRAM_GB,
                    is_installed=True,
                    digest=m.get("digest", "")[:12],
                ))
            self._models_cache = models
            return models
        except Exception as e:
            return []

    def _estimate_vram(self, name: str, size_gb: float) -> float:
        # Check exact match first
        for key, vram in VRAM_ESTIMATES.items():
            if name.startswith(key) or key in name:
                return vram
        # Heuristic: VRAM ≈ 1.2× model size (quantized) + 0.5GB overhead
        return size_gb * 1.2 + 0.5

    async def pull_model(self, model_name: str):
        """Async generator that yields pull progress lines."""
        import json
        async with self._client.stream(
            "POST",
            f"{self._base_url}/api/pull",
            json={"name": model_name, "stream": True},
            timeout=3600.0,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.strip():
                    try:
                        yield json.loads(line)
                    except Exception:
                        yield {"status": line}

    async def is_ollama_running(self) -> bool:
        try:
            resp = await self._client.get(f"{self._base_url}/api/version", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def get_version(self) -> str:
        try:
            resp = await self._client.get(f"{self._base_url}/api/version", timeout=3.0)
            return resp.json().get("version", "unknown")
        except Exception:
            return "unavailable"

    async def close(self) -> None:
        await self._client.aclose()
