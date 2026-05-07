import httpx

from app.llm.base import ChatMessage, LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible chat completion. Works for OpenAI, DeepSeek, DashScope-compatible endpoints."""

    name = "openai"
    default_model = "gpt-4o-mini"

    async def chat(self, messages: list[ChatMessage], *, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        url = (self.base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
        return data["choices"][0]["message"]["content"]


class DeepSeekProvider(OpenAIProvider):
    name = "deepseek"
    default_model = "deepseek-chat"

    def __init__(self, api_key: str, model: str | None = None, base_url: str | None = None):
        super().__init__(api_key=api_key, model=model, base_url=base_url or "https://api.deepseek.com/v1")


class DashScopeProvider(OpenAIProvider):
    """Aliyun Tongyi Qianwen via OpenAI-compatible mode."""

    name = "dashscope"
    default_model = "qwen-plus"

    def __init__(self, api_key: str, model: str | None = None, base_url: str | None = None):
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
