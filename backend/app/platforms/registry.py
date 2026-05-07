from app.platforms.base import PlatformAdapter
from app.platforms.twitter import TwitterAdapter

_ADAPTERS: dict[str, type[PlatformAdapter]] = {
    "twitter": TwitterAdapter,
    # Future: "weibo": WeiboAdapter, "xiaohongshu": XiaohongshuAdapter, ...
}


def build_adapter(platform: str, credentials: dict) -> PlatformAdapter:
    cls = _ADAPTERS.get(platform)
    if cls is None:
        raise ValueError(f"Unsupported platform: {platform}")
    return cls(credentials=credentials)


def supported_platforms() -> list[str]:
    return list(_ADAPTERS.keys())
