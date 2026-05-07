from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMProvider(ABC):
    name: str = ""
    default_model: str = ""

    def __init__(self, api_key: str, model: str | None = None, base_url: str | None = None):
        self.api_key = api_key
        self.model = model or self.default_model
        self.base_url = base_url

    @abstractmethod
    async def chat(self, messages: list[ChatMessage], *, temperature: float = 0.7, max_tokens: int = 1024) -> str: ...
