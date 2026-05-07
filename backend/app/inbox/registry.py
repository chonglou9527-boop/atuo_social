from app.inbox.base import InboxFetcher
from app.inbox.rss import RSSFetcher
from app.inbox.twitter_list import TwitterListFetcher

_FETCHERS: dict[str, type[InboxFetcher]] = {
    "rss": RSSFetcher,
    "twitter_list": TwitterListFetcher,
}


def build_fetcher(type_name: str, config: dict) -> InboxFetcher:
    cls = _FETCHERS.get(type_name)
    if cls is None:
        raise ValueError(f"Unknown inbox source type: {type_name}")
    return cls(config=config)


def supported_types() -> list[str]:
    return list(_FETCHERS.keys())
