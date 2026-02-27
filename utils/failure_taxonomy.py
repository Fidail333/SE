from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FailureCategory:
    key: str
    name: str
    message_regex: str
    patterns: tuple[re.Pattern[str], ...]


def _compile_patterns(values: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(value, re.IGNORECASE) for value in values)


_INFRA_PATTERNS = _compile_patterns(
    (
        r"ddos[- ]?guard|cloudflare|captcha|verify you are human|access denied|антибот|капча",
        r"name or service not known|getaddrinfo|temporary failure in name resolution|dns",
        r"timeout|timed out|err_network|err_timed_out|ns_error_net_timeout|network reset|connection reset",
        r"target page, context or browser has been closed",
    )
)

_TEST_PATTERNS = _compile_patterns(
    (
        r"locator expected to be visible|strict mode violation|to_be_visible",
        r"attributeerror|typeerror|keyerror|indexerror",
        r"не найден .*селектор|invalid rule profile|rules? mismatch",
        r"playwright\.sync_api\.Error",
    )
)

_PRODUCT_PATTERNS = _compile_patterns(
    (
        r"\b5\d\d\b|final status should be 200|5xx response",
        r"контентн\w* инвариант|seo-инвариант|canonical|meta robots|title.*empty|body too short",
        r"negative url.*404/410|unexpected content-type|tag <html is missing|tag <body is missing",
    )
)


FAILURE_CATEGORIES: tuple[FailureCategory, ...] = (
    FailureCategory(
        key="infra",
        name="Infra/Access",
        message_regex=(
            "(?i)(ddos[- ]?guard|cloudflare|captcha|verify you are human|access denied|антибот|капча|"
            "dns|getaddrinfo|temporary failure in name resolution|timeout|timed out|err_network|err_timed_out|"
            "ns_error_net_timeout|network reset|connection reset)"
        ),
        patterns=_INFRA_PATTERNS,
    ),
    FailureCategory(
        key="test",
        name="Test defects",
        message_regex=(
            "(?i)(locator expected to be visible|strict mode violation|to_be_visible|attributeerror|typeerror|"
            "keyerror|indexerror|не найден .*селектор|invalid rule profile|rules? mismatch|playwright\\.sync_api\\.Error)"
        ),
        patterns=_TEST_PATTERNS,
    ),
    FailureCategory(
        key="product",
        name="Product defects",
        message_regex=(
            "(?i)(\\b5\\d\\d\\b|final status should be 200|5xx response|контентн\\w* инвариант|seo-инвариант|"
            "canonical|meta robots|title.*empty|body too short|negative url.*404/410|unexpected content-type|"
            "tag <html is missing|tag <body is missing)"
        ),
        patterns=_PRODUCT_PATTERNS,
    ),
)


UNCATEGORIZED_KEY = "uncategorized"


def classify_failure_text(text: str) -> str:
    if not text:
        return UNCATEGORIZED_KEY

    for category in FAILURE_CATEGORIES:
        if any(pattern.search(text) for pattern in category.patterns):
            return category.key
    return UNCATEGORIZED_KEY


def build_allure_categories_payload() -> list[dict[str, object]]:
    categories: list[dict[str, object]] = []
    for category in FAILURE_CATEGORIES:
        categories.append(
            {
                "name": category.name,
                "matchedStatuses": ["failed", "broken"],
                "messageRegex": category.message_regex,
            }
        )
    categories.append(
        {
            "name": "Uncategorized failures",
            "matchedStatuses": ["failed", "broken"],
        }
    )
    return categories
