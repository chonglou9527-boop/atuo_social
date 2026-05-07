"""Minimal smoke tests covering wiring, encryption, rule matching, RSS parsing."""
from __future__ import annotations

import json

import pytest

from app.core.security import decrypt, encrypt
from app.db.models import InboxItem, RewriteRule
from app.services.rewrite import _matches  # noqa: PLC2701 (testing private helper)


def test_encrypt_roundtrip():
    token = encrypt("hello-世界")
    assert decrypt(token) == "hello-世界"


def test_app_starts():
    from app.main import app  # noqa: PLC0415

    assert app.title


def test_llm_registry():
    from app.llm.registry import build_provider, list_providers  # noqa: PLC0415

    assert "anthropic" in list_providers()
    p = build_provider("anthropic", api_key="dummy")
    assert p.name == "anthropic"


def test_platform_registry():
    from app.platforms.registry import build_adapter, supported_platforms  # noqa: PLC0415

    assert "twitter" in supported_platforms()
    a = build_adapter("twitter", {"consumer_key": "x", "consumer_secret": "x", "access_token": "x", "access_token_secret": "x"})
    assert a.platform == "twitter"


def test_rule_matching():
    item = InboxItem(
        source_id=1,
        external_id="e1",
        title="OpenAI 发布新模型",
        content="今天 OpenAI 公布了 GPT-X ...",
        tags_json=["AI", "Model"],
    )
    r1 = RewriteRule(name="ai", keywords_json=["openai", "gpt"], tags_json=[], source_ids_json=[])
    assert _matches(item, r1) is True

    r2 = RewriteRule(name="tag", tags_json=["sports"], keywords_json=[], source_ids_json=[])
    assert _matches(item, r2) is False

    r3 = RewriteRule(name="src", source_ids_json=[2], keywords_json=[], tags_json=[])
    assert _matches(item, r3) is False


def test_inbox_source_types():
    from app.inbox.registry import supported_types  # noqa: PLC0415

    assert {"rss", "twitter_list"}.issubset(set(supported_types()))


def test_rss_parser_basic():
    pytest.importorskip("feedparser")
    from app.inbox.rss import _parse_date  # noqa: PLC0415

    class E(dict):
        def __getattr__(self, k):
            return self[k]

    e = E({"published": "Wed, 02 Oct 2024 14:00:00 GMT"})
    assert _parse_date(e) is not None
