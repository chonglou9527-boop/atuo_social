from anthropic import AsyncAnthropic

from app.llm.base import ChatMessage, LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    default_model = "claude-sonnet-4-6"

    async def chat(self, messages: list[ChatMessage], *, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        client = AsyncAnthropic(api_key=self.api_key, base_url=self.base_url) if self.base_url else AsyncAnthropic(api_key=self.api_key)

        system = "\n".join(m.content for m in messages if m.role == "system") or None
        chat_msgs = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in {"user", "assistant"}
        ]

        kwargs = {"model": self.model, "max_tokens": max_tokens, "temperature": temperature, "messages": chat_msgs}
        if system:
            kwargs["system"] = system

        resp = await client.messages.create(**kwargs)
        return "".join(block.text for block in resp.content if getattr(block, "type", None) == "text")
