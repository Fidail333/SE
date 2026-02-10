from __future__ import annotations

import json
from collections.abc import Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from core.config import Settings, get_settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright, settings: Settings) -> Generator[Browser, None, None]:
    browser_type = getattr(playwright_instance, settings.browser)
    browser = browser_type.launch(headless=settings.headless, slow_mo=settings.slowmo_ms)
    yield browser
    browser.close()


@pytest.fixture()
def context(browser: Browser, settings: Settings) -> Generator[BrowserContext, None, None]:
    context = browser.new_context(
        viewport={"width": 1600, "height": 1000},
        ignore_https_errors=True,
        locale="ru-RU",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    context.set_default_timeout(settings.default_timeout_ms)
    context.set_default_navigation_timeout(settings.navigation_timeout_ms)
    yield context
    context.close()


@pytest.fixture()
def page(context: BrowserContext) -> Generator[Page, None, None]:
    console_messages: list[str] = []
    request_failures: list[dict[str, str]] = []

    page = context.new_page()
    page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
    page.on(
        "requestfailed",
        lambda request: request_failures.append(
            {
                "url": request.url,
                "method": request.method,
                "failure": request.failure or "unknown",
            }
        ),
    )

    page.console_messages = console_messages  # type: ignore[attr-defined]
    page.request_failures = request_failures  # type: ignore[attr-defined]
    yield page
    page.close()


@pytest.fixture()
def network_summary(page: Page) -> str:
    failures = getattr(page, "request_failures", [])
    return json.dumps(failures, ensure_ascii=False, indent=2)
