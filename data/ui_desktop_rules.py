from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern
from urllib.parse import urlparse


@dataclass(frozen=True)
class DesktopRule:
    profile: str
    require_h1: bool = False
    require_content_block: bool = False
    content_selectors: tuple[str, ...] = ()
    require_any_visible: tuple[str, ...] = ()
    min_links_in_content: int = 0


@dataclass(frozen=True)
class UrlDesktopRule:
    rule: DesktopRule
    reason: str
    exact_url: str | None = None
    path_regex: Pattern[str] | None = None

    def matches(self, url: str, path: str) -> bool:
        return (self.exact_url == url) or bool(self.path_regex and self.path_regex.search(path))


@dataclass(frozen=True)
class ResolvedDesktopRule:
    rule: DesktopRule
    is_special: bool
    reason: str | None = None


LISTING_RULE = DesktopRule(
    profile="home/section/listing",
    require_any_visible=("main", "article", "[role='main']"),
    min_links_in_content=1,
)

ARTICLE_RULE = DesktopRule(
    profile="article-like",
    require_h1=True,
    require_content_block=True,
    content_selectors=(
        "article p",
        ".article p",
        "[itemprop='articleBody'] p",
        "main p",
    ),
    require_any_visible=("main", "article", "[role='main']"),
)

STATS_RULE = DesktopRule(
    profile="stats/live/matchcenter",
    require_any_visible=(
        "h1",
        "table",
        "[class*='table']",
        "[class*='widget']",
        "[data-widget]",
        "[data-testid*='table']",
    ),
)

SERVICE_RULE = DesktopRule(
    profile="service",
    require_any_visible=(
        "h1",
        "form",
        "main",
        "article",
        "[role='main']",
        ".content",
        ".page-content",
    ),
)

SPECIAL_DYNAMIC_RULE = DesktopRule(
    profile="stats/live-special",
    require_any_visible=(
        "main",
        "article",
        "[role='main']",
        "table",
        "[class*='table']",
        "[class*='widget']",
    ),
)


SPECIAL_URL_RULES: tuple[UrlDesktopRule, ...] = (
    UrlDesktopRule(
        exact_url="https://www.sport-express.ru/fighting/mma/ufc/2024/ratings/men/",
        rule=SPECIAL_DYNAMIC_RULE,
        reason="Dynamic ratings page can have non-standard desktop layout.",
    ),
    UrlDesktopRule(
        exact_url="https://www.sport-express.ru/hockey/L/khl/2023-2024/stadiums/",
        rule=SPECIAL_DYNAMIC_RULE,
        reason="Dynamic stats page can have non-standard desktop layout.",
    ),
    UrlDesktopRule(
        exact_url="https://www.sport-express.ru/hockey/L/khl/2023-2024/teams/",
        rule=SPECIAL_DYNAMIC_RULE,
        reason="Dynamic stats page can have non-standard desktop layout.",
    ),
    UrlDesktopRule(
        exact_url="https://www.sport-express.ru/hockey/L/khl/2023-2024/trainers/",
        rule=SPECIAL_DYNAMIC_RULE,
        reason="Dynamic stats page can have non-standard desktop layout.",
    ),
    UrlDesktopRule(
        exact_url="https://www.sport-express.ru/hockey/L/matchcenter/112783/",
        rule=SPECIAL_DYNAMIC_RULE,
        reason="Matchcenter endpoint can have non-standard desktop layout.",
    ),
)

PATH_RULES: tuple[UrlDesktopRule, ...] = (
    UrlDesktopRule(
        path_regex=re.compile(
            r"^/(search|registration|subscribe)(/|$)|"
            r"^/(company|advert)(/|$)|"
            r"^/(projects/apps|brend-centr|editorial|stavki-na-sport)(/|$)",
            re.IGNORECASE,
        ),
        rule=SERVICE_RULE,
        reason="Service-like page.",
    ),
    UrlDesktopRule(
        path_regex=re.compile(r"/l/|/matchcenter/|^/live(/|$)|/fbl_match-", re.IGNORECASE),
        rule=STATS_RULE,
        reason="Stats/live/matchcenter page.",
    ),
    UrlDesktopRule(
        path_regex=re.compile(
            r"/(news|reviews|stories|online|poll|photoreports|videoreports|materials)/|-\d{5,}/?$",
            re.IGNORECASE,
        ),
        rule=ARTICLE_RULE,
        reason="Article-like page.",
    ),
)


def resolve_desktop_rule(url: str) -> ResolvedDesktopRule:
    path = urlparse(url).path or "/"

    for url_rule in SPECIAL_URL_RULES:
        if url_rule.matches(url=url, path=path):
            return ResolvedDesktopRule(rule=url_rule.rule, is_special=True, reason=url_rule.reason)

    for url_rule in PATH_RULES:
        if url_rule.matches(url=url, path=path):
            return ResolvedDesktopRule(rule=url_rule.rule, is_special=False, reason=url_rule.reason)

    return ResolvedDesktopRule(rule=LISTING_RULE, is_special=False, reason="Default listing-like page.")
