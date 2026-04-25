"""Abstract LLM interface - adapter pattern for model independence."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator


@dataclass
class LLMRequest:
    prompt: str
    system: str = ""
    temperature: float = 0.8
    max_tokens: int = 512
    stream: bool = False


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int = 0
    duration_ms: float = 0.0


class LLMInterface(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...
