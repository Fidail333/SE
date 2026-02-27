from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

import allure
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, expect

from data.ui_desktop_rules import ResolvedDesktopRule, resolve_desktop_rule

_BASE_CONTENT_SELECTORS = ("main", "article", "[role='main']")
_ANTIBOT_MARKERS = (
    "access denied",
    "captcha",
    "cloudflare",
    "ddos",
    "verify you are human",
    "проверка, что вы не робот",
    "доступ временно ограничен",
    "подозрительная активность",
)
_STRUCTURE_FALLBACK_SELECTORS = (
    "h1",
    "h2",
    "a[href]",
    "table",
    "form",
    "#content",
    "#main",
    ".content",
    ".wrapper",
    ".container",
)
_LISTING_CARD_SELECTORS = (
    "main article",
    "main [class*='card']",
    "main [class*='item']",
    "main a[href]",
)
_GLOBAL_ALLOWED_CONSOLE_ERROR_PATTERNS = (
    "ResizeObserver loop limit exceeded",
    "Script error",
)
_GLOBAL_IGNORED_FAILED_REQUEST_PATTERNS = (
    "googletagmanager",
    "doubleclick",
    "google-analytics",
    "mc.yandex",
    "top-fwz1.mail.ru",
    "/ads",
    "favicon.ico",
)
_PLACEHOLDER_ANTI_PATTERNS = (
    re.compile(r"\bundefined\b", re.IGNORECASE),
    re.compile(r"\bnull\b", re.IGNORECASE),
    re.compile(r"lorem ipsum", re.IGNORECASE),
    re.compile(r"ошибка загрузки", re.IGNORECASE),
    re.compile(r"something went wrong", re.IGNORECASE),
)


@dataclass(frozen=True)
class JSNetworkContext:
    console_events: list[dict[str, str]]
    request_failures: list[dict[str, str]]


def resolve_rule_for_url(url: str) -> ResolvedDesktopRule:
    return resolve_desktop_rule(url)


def attach_rule_payload(url: str, resolved: ResolvedDesktopRule) -> None:
    payload = {
        "url": url,
        "profile": resolved.rule.profile,
        "is_special": resolved.is_special,
        "reason": resolved.reason,
        "require_h1": resolved.rule.require_h1,
        "require_content_block": resolved.rule.require_content_block,
        "require_seo_checks": resolved.rule.require_seo_checks,
        "require_content_checks": resolved.rule.require_content_checks,
        "require_js_health_checks": resolved.rule.require_js_health_checks,
        "require_any_visible": list(resolved.rule.require_any_visible),
        "content_selectors": list(resolved.rule.content_selectors),
        "min_links_in_content": resolved.rule.min_links_in_content,
        "allowed_console_error_patterns": list(resolved.rule.allowed_console_error_patterns),
        "ignored_failed_request_patterns": list(resolved.rule.ignored_failed_request_patterns),
    }
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name="desktop_rules",
        attachment_type=allure.attachment_type.JSON,
    )


def attach_navigation_payload(page: Page, requested_url: str, response_status: int | None = None) -> None:
    payload = {
        "requested_url": requested_url,
        "final_url": page.url,
        "status_code": response_status,
        "title": _safe_title(page),
    }
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name="navigation",
        attachment_type=allure.attachment_type.JSON,
    )


def collect_js_network_context(page: Page) -> JSNetworkContext:
    console_events = list(getattr(page, "_se_console_events", []))
    request_failures = list(getattr(page, "_se_request_failures", []))
    return JSNetworkContext(console_events=console_events, request_failures=request_failures)


def attach_js_network_summary(page: Page) -> JSNetworkContext:
    context = collect_js_network_context(page)
    console_errors = [entry for entry in context.console_events if entry.get("type", "").lower() == "error"]
    payload = {
        "console_total": len(context.console_events),
        "console_errors": len(console_errors),
        "request_failed_total": len(context.request_failures),
        "sample_console_errors": console_errors[:10],
        "sample_request_failures": context.request_failures[:10],
    }
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name="js_network_summary",
        attachment_type=allure.attachment_type.JSON,
    )
    return context


def assert_no_antibot(page: Page) -> None:
    title = _safe_title(page).lower()
    body_text = _safe_body_text(page).lower()

    for marker in _ANTIBOT_MARKERS:
        if marker in title or marker in body_text:
            raise AssertionError(
                "Обнаружена антибот-защита/капча. "
                f"marker='{marker}', url='{page.url}', title='{_safe_title(page)}'"
            )


def assert_base_desktop_structure(page: Page) -> None:
    expect(page.locator("body")).to_be_visible()
    matched_selector = _first_visible_selector(page=page, selectors=_BASE_CONTENT_SELECTORS)
    if not matched_selector:
        if _has_meaningful_render(page):
            allure.attach(
                "Базовый контейнер main/article не найден, но страница отрисована (fallback).",
                name="base_structure_fallback",
                attachment_type=allure.attachment_type.TEXT,
            )
            return
        raise AssertionError(
            "Не найден базовый desktop контейнер, и fallback-проверка не подтвердила отрисовку страницы. "
            f"Ожидались селекторы: {', '.join(_BASE_CONTENT_SELECTORS)}"
        )


def assert_profile_structure(page: Page, resolved: ResolvedDesktopRule) -> None:
    rule = resolved.rule

    if rule.require_h1:
        expect(page.get_by_role("heading", level=1).first).to_be_visible()

    if rule.require_content_block:
        matched_content_selector = _first_visible_selector(page=page, selectors=rule.content_selectors)
        if not matched_content_selector:
            if _has_meaningful_render(page):
                allure.attach(
                    (
                        "Контентный блок по строгим селекторам не найден, но страница содержит "
                        "значимый контент (fallback)."
                    ),
                    name="profile_content_fallback",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                raise AssertionError(
                    "Не найден контентный блок для article-like страницы. "
                    f"Проверены селекторы: {', '.join(rule.content_selectors)}"
                )

    if rule.require_any_visible:
        matched_selector = _first_visible_selector(page=page, selectors=rule.require_any_visible)
        if not matched_selector:
            if _has_meaningful_render(page):
                allure.attach(
                    (
                        "Не найден обязательный селектор профиля, но страница содержит "
                        "значимый контент (fallback)."
                    ),
                    name="profile_selector_fallback",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                raise AssertionError(
                    "Не найден ни один обязательный селектор профиля. "
                    f"Профиль='{rule.profile}', селекторы={', '.join(rule.require_any_visible)}"
                )

    if rule.min_links_in_content > 0:
        links_count = _count_content_links(page)
        if links_count < rule.min_links_in_content:
            if _has_meaningful_render(page):
                allure.attach(
                    (
                        f"Ссылок в контенте меньше ожидаемого ({links_count} < {rule.min_links_in_content}), "
                        "но страница содержит значимый контент (fallback)."
                    ),
                    name="profile_links_fallback",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                raise AssertionError(
                    "Недостаточно ссылок в основном контенте. "
                    f"Ожидалось >= {rule.min_links_in_content}, получено {links_count}"
                )


def assert_seo_invariants(page: Page, resolved: ResolvedDesktopRule) -> None:
    rule = resolved.rule
    if not rule.require_seo_checks:
        return

    title = _safe_title(page).strip()
    assert title, "SEO: title пустой"
    assert 3 <= len(title) <= 180, f"SEO: title имеет невалидную длину: {len(title)}"

    current_host = urlparse(page.url).netloc.lower()
    canonical_locator = page.locator("link[rel='canonical']").first
    canonical_required = rule.profile not in {"service"}

    if canonical_locator.count() == 0:
        if canonical_required:
            raise AssertionError("SEO: canonical отсутствует")
    else:
        canonical_href = (canonical_locator.get_attribute("href") or "").strip()
        assert canonical_href, "SEO: canonical href пустой"
        parsed = urlparse(canonical_href)
        if parsed.scheme and parsed.netloc:
            canonical_host = parsed.netloc.lower()
            assert canonical_host == current_host, (
                f"SEO: canonical host '{canonical_host}' отличается от текущего '{current_host}'"
            )
        elif not canonical_href.startswith("/"):
            raise AssertionError(f"SEO: canonical должен быть абсолютным URL или относительным путём, got={canonical_href}")

    robots_locator = page.locator("meta[name='robots' i]").first
    if robots_locator.count() > 0:
        robots_value = (robots_locator.get_attribute("content") or "").strip().lower()
        assert robots_value, "SEO: meta robots присутствует, но content пустой"
        allowed_tokens = ("index", "noindex", "follow", "nofollow")
        if not any(token in robots_value for token in allowed_tokens):
            raise AssertionError(f"SEO: meta robots имеет подозрительное значение: '{robots_value}'")


def assert_content_invariants(page: Page, resolved: ResolvedDesktopRule) -> None:
    rule = resolved.rule
    if not rule.require_content_checks:
        return

    body_text = _safe_body_text(page)
    lower_body = body_text.lower()
    for pattern in _PLACEHOLDER_ANTI_PATTERNS:
        if pattern.search(lower_body):
            raise AssertionError(f"Content: найден placeholder-антипаттерн '{pattern.pattern}'")

    if rule.profile == "article-like":
        has_h1 = _first_visible_selector(page, ("h1", "[itemprop='headline']", "article h1")) is not None
        has_content = _first_visible_selector(page, rule.content_selectors) is not None
        if not (has_h1 or has_content or _has_meaningful_render(page)):
            raise AssertionError("Content: article-like страница не содержит заголовок/контентный блок")
        if len(body_text.strip()) < 120 and not has_content:
            raise AssertionError("Content: article-like страница содержит слишком мало текстового контента")

    if rule.profile == "home/section/listing":
        has_cards = _first_visible_selector(page, _LISTING_CARD_SELECTORS) is not None
        links_count = _safe_links_count(page)
        if not has_cards and links_count < 3 and not _has_meaningful_render(page):
            raise AssertionError("Content: listing страница не содержит карточки/ссылки контента")

    if rule.profile.startswith("stats/live"):
        has_stats = _first_visible_selector(page, ("table", "[class*='table']", "[class*='widget']", "h1"))
        if not has_stats and not _has_meaningful_render(page):
            raise AssertionError("Content: stats/live страница не содержит ожидаемые элементы статистики")


def assert_js_health(
    page: Page,
    resolved: ResolvedDesktopRule,
    context_data: JSNetworkContext | None = None,
) -> None:
    rule = resolved.rule
    if not rule.require_js_health_checks:
        return

    context = context_data or collect_js_network_context(page)

    allowed_console_patterns = _GLOBAL_ALLOWED_CONSOLE_ERROR_PATTERNS + rule.allowed_console_error_patterns
    ignored_request_patterns = _GLOBAL_IGNORED_FAILED_REQUEST_PATTERNS + rule.ignored_failed_request_patterns

    critical_console_errors: list[dict[str, str]] = []
    for entry in context.console_events:
        event_type = entry.get("type", "").lower()
        text = entry.get("text", "")
        if event_type != "error":
            continue
        if _matches_any_pattern(text, allowed_console_patterns):
            continue
        critical_console_errors.append(entry)

    critical_request_failures: list[dict[str, str]] = []
    for entry in context.request_failures:
        target = f"{entry.get('url', '')} {entry.get('failure', '')}"
        if _matches_any_pattern(target, ignored_request_patterns):
            continue
        critical_request_failures.append(entry)

    if critical_console_errors or critical_request_failures:
        payload = {
            "critical_console_errors": critical_console_errors[:10],
            "critical_request_failures": critical_request_failures[:10],
        }
        allure.attach(
            json.dumps(payload, ensure_ascii=False, indent=2),
            name="js_network_critical",
            attachment_type=allure.attachment_type.JSON,
        )
        raise AssertionError(
            "JS/Network health: обнаружены критичные ошибки. "
            f"console={len(critical_console_errors)}, request_failed={len(critical_request_failures)}"
        )


def _safe_links_count(page: Page) -> int:
    try:
        return page.locator("a[href]").count()
    except PlaywrightError:
        return 0


def _count_content_links(page: Page) -> int:
    for selector in _BASE_CONTENT_SELECTORS:
        locator = page.locator(selector).first
        if locator.count() == 0:
            continue
        try:
            if locator.is_visible(timeout=3000):
                return locator.locator("a[href]").count()
        except PlaywrightError:
            continue
    return 0


def _first_visible_selector(page: Page, selectors: Iterable[str]) -> str | None:
    for selector in selectors:
        locator = page.locator(selector).first
        if locator.count() == 0:
            continue
        try:
            if locator.is_visible(timeout=3000):
                return selector
        except PlaywrightError:
            continue
    return None


def _safe_title(page: Page) -> str:
    try:
        return page.title()
    except PlaywrightError:
        return ""


def _safe_body_text(page: Page) -> str:
    try:
        return page.locator("body").inner_text(timeout=3000)
    except PlaywrightError:
        return ""


def _matches_any_pattern(value: str, patterns: Iterable[str]) -> bool:
    lowered = value.lower()
    return any(pattern.lower() in lowered for pattern in patterns if pattern)


def _has_meaningful_render(page: Page) -> bool:
    if _first_visible_selector(page=page, selectors=_STRUCTURE_FALLBACK_SELECTORS):
        return True

    body_text = _safe_body_text(page).strip()
    if len(body_text) >= 120:
        return True

    return _safe_links_count(page) >= 3
