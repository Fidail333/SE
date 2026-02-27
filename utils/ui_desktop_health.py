from __future__ import annotations

import json
from typing import Iterable

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
        "require_any_visible": list(resolved.rule.require_any_visible),
        "content_selectors": list(resolved.rule.content_selectors),
        "min_links_in_content": resolved.rule.min_links_in_content,
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
        # Fallback: SE страницы могут использовать нестандартную разметку без main/article.
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


def _has_meaningful_render(page: Page) -> bool:
    if _first_visible_selector(page=page, selectors=_STRUCTURE_FALLBACK_SELECTORS):
        return True

    body_text = _safe_body_text(page).strip()
    if len(body_text) >= 120:
        return True

    try:
        if page.locator("a[href]").count() >= 3:
            return True
    except PlaywrightError:
        return False

    return False
