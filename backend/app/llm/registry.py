from app.llm.anthropic import AnthropicProvider
from app.llm.base import LLMProvider
from app.llm.openai import DashScopeProvider, DeepSeekProvider, OpenAIProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
    "dashscope": DashScopeProvider,
}


def build_provider(provider: str, api_key: str, model: str | None = None, base_url: str | None = None) -> LLMProvider:
    cls = _PROVIDERS.get(provider)
    if cls is None:
        raise ValueError(f"Unknown LLM provider: {provider}")
    return cls(api_key=api_key, model=model, base_url=base_url)


def list_providers() -> list[str]:
    return list(_PROVIDERS.keys())
