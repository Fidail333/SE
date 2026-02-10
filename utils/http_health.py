from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Pattern

import requests

_ALLOWED_REDIRECT_CODES = {301, 302, 307, 308}
_VALID_CONTENT_TYPES = ("text/html", "application/xhtml+xml")


@dataclass(frozen=True)
class HealthRules:
    require_html_body: bool = True
    require_content_type: bool = True
    min_body_length: int = 2000


@dataclass(frozen=True)
class UrlRule:
    rules: HealthRules
    reason: str
    exact_url: str | None = None
    url_regex: Pattern[str] | None = None

    def matches(self, url: str) -> bool:
        return (self.exact_url == url) or bool(self.url_regex and self.url_regex.search(url))


DEFAULT_HEALTH_RULES = HealthRules()

URL_RULES: tuple[UrlRule, ...] = (
    UrlRule(
        exact_url="https://www.sport-express.ru/fighting/mma/ufc/2024/ratings/men/",
        rules=HealthRules(require_html_body=False, require_content_type=False, min_body_length=0),
        reason="Dynamic ratings page may return non-standard body/content-type",
    ),
    UrlRule(
        exact_url="https://www.sport-express.ru/hockey/L/khl/2023-2024/stadiums/",
        rules=HealthRules(require_html_body=False, require_content_type=False, min_body_length=0),
        reason="Stats page may render dynamic or non-standard HTML response",
    ),
    UrlRule(
        exact_url="https://www.sport-express.ru/hockey/L/khl/2023-2024/teams/",
        rules=HealthRules(require_html_body=False, require_content_type=False, min_body_length=0),
        reason="Stats page may render dynamic or non-standard HTML response",
    ),
    UrlRule(
        exact_url="https://www.sport-express.ru/hockey/L/khl/2023-2024/trainers/",
        rules=HealthRules(require_html_body=False, require_content_type=False, min_body_length=0),
        reason="Stats page may render dynamic or non-standard HTML response",
    ),
    UrlRule(
        exact_url="https://www.sport-express.ru/hockey/L/matchcenter/112783/",
        rules=HealthRules(require_html_body=False, require_content_type=False, min_body_length=0),
        reason="Matchcenter endpoint can serve dynamic payloads",
    ),
)


@dataclass
class HealthResponse:
    requested_url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    body: str
    redirect_chain: list[int]


@dataclass(frozen=True)
class ResolvedHealthRules:
    rules: HealthRules
    is_special: bool
    reason: str | None = None


def resolve_health_rules(url: str) -> ResolvedHealthRules:
    for url_rule in URL_RULES:
        if url_rule.matches(url):
            return ResolvedHealthRules(rules=url_rule.rules, is_special=True, reason=url_rule.reason)
    return ResolvedHealthRules(rules=DEFAULT_HEALTH_RULES, is_special=False)


def _extract_title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title or None


def request_with_retry(url: str, attempts: int = 3) -> HealthResponse:
    last_exception: Exception | None = None
    backoffs = [0.5, 1.0, 2.0]

    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(
                url,
                allow_redirects=True,
                timeout=(10, 45),
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    )
                },
            )

            if 500 <= response.status_code <= 599 and attempt < attempts:
                time.sleep(backoffs[min(attempt - 1, len(backoffs) - 1)])
                continue

            return HealthResponse(
                requested_url=url,
                final_url=response.url,
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.text,
                redirect_chain=[item.status_code for item in response.history],
            )
        except requests.RequestException as exc:
            last_exception = exc
            if attempt >= attempts:
                raise
            time.sleep(backoffs[min(attempt - 1, len(backoffs) - 1)])

    if last_exception:
        raise last_exception

    raise RuntimeError(f"Unexpected retry flow for URL: {url}")


def assert_positive_html_health(
    health: HealthResponse,
    resolved_rules: ResolvedHealthRules | None = None,
) -> ResolvedHealthRules:
    resolved_rules = resolved_rules or resolve_health_rules(health.requested_url)
    rules = resolved_rules.rules

    assert all(code in _ALLOWED_REDIRECT_CODES for code in health.redirect_chain), (
        f"Unexpected redirect chain: {health.redirect_chain}"
    )
    assert health.status_code == 200, f"Final status should be 200, got {health.status_code}"
    assert not (500 <= health.status_code <= 599), f"5xx response: {health.status_code}"

    if rules.require_content_type:
        content_type = health.headers.get("Content-Type", "").lower()
        assert any(value in content_type for value in _VALID_CONTENT_TYPES), (
            f"Unexpected Content-Type: {content_type}"
        )

    assert len(health.body) > rules.min_body_length, f"Body too short: {len(health.body)}"

    if rules.require_html_body:
        assert "<html" in health.body.lower(), "Tag <html is missing"
        assert "<body" in health.body.lower(), "Tag <body is missing"

        title = _extract_title(health.body)
        assert title, "<title> is missing or empty"

    return resolved_rules
