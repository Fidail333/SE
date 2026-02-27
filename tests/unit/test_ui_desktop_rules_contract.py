from __future__ import annotations

from data.ui_desktop_rules import resolve_desktop_rule
from data.urls import URL_CASES


ALLOWED_PROFILES = {
    "home/section/listing",
    "article-like",
    "stats/live/matchcenter",
    "stats/live-special",
    "service",
}


def test_all_url_cases_resolve_to_supported_profile() -> None:
    for url in URL_CASES:
        resolved = resolve_desktop_rule(url)
        assert resolved.rule.profile in ALLOWED_PROFILES, f"Unexpected profile for {url}: {resolved.rule.profile}"


def test_profile_resolution_is_stable_for_same_url() -> None:
    for url in URL_CASES:
        first = resolve_desktop_rule(url)
        second = resolve_desktop_rule(url)
        assert first == second, f"Resolution is not deterministic for {url}"


def test_known_profile_mapping_examples() -> None:
    article = "https://www.sport-express.ru/rating-bookmakerov/news/reyting-bukmekerov-1989757/"
    service = "https://www.sport-express.ru/company/rss/"
    stats = "https://www.sport-express.ru/football/L/russia/premier/2023-2024/"

    assert resolve_desktop_rule(article).rule.profile == "article-like"
    assert resolve_desktop_rule(service).rule.profile == "service"
    assert resolve_desktop_rule(stats).rule.profile in {"stats/live/matchcenter", "stats/live-special"}
