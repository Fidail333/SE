from __future__ import annotations

from urllib.parse import urljoin

import allure
import pytest
from playwright.sync_api import Locator, Page, expect

from core.config import get_settings


class BasePage:
    _DEFAULT_PAGE_ANCHOR_SELECTORS = ("header", "nav", "main", "h1")

    def __init__(self, page: Page) -> None:
        self.page = page
        self.settings = get_settings()

    def open_path(self, path: str = "/") -> None:
        target = urljoin(f"{self.settings.base_url}/", path.lstrip("/"))
        navigation_timeout_ms = max(self.settings.navigation_timeout_ms, 30000)
        with allure.step(f"Открыть URL: {target}"):
            self.page.goto(target, wait_until="domcontentloaded", timeout=navigation_timeout_ms)
            self.page.wait_for_load_state("load", timeout=navigation_timeout_ms)
            self.wait_for_page_anchor(timeout_ms=navigation_timeout_ms)
            self._handle_overlays()
            self._skip_if_antibot_detected()

    def wait_ready(self) -> None:
        expect(self.page.locator("body")).to_be_visible()

    def wait_for_page_anchor(
        self,
        timeout_ms: int | None = None,
        selectors: tuple[str, ...] | None = None,
    ) -> None:
        timeout = timeout_ms or max(self.settings.navigation_timeout_ms, 30000)
        anchor_selectors = selectors or self._DEFAULT_PAGE_ANCHOR_SELECTORS

        with allure.step(f"Дождаться якорного элемента страницы: {', '.join(anchor_selectors)}"):
            for selector in anchor_selectors:
                anchor = self.page.locator(selector).first
                if anchor.count() > 0:
                    expect(anchor).to_be_visible(timeout=timeout)
                    return

        raise AssertionError(
            "Не найден якорный элемент после навигации. "
            f"Проверены селекторы: {', '.join(anchor_selectors)}"
        )

    def _handle_overlays(self) -> None:
        with allure.step("Проверить и закрыть cookie/pop-up баннеры (если есть)"):
            selectors = [
                "button:has-text('Принять')",
                "button:has-text('Согласен')",
                "button:has-text('Понятно')",
                "button:has-text('ОК')",
                "button:has-text('Accept')",
                "button:has-text('I agree')",
                "[aria-label*='close' i]",
                "[aria-label*='закры' i]",
                ".cookie button",
                "#onetrust-accept-btn-handler",
            ]
            for selector in selectors:
                locator = self.page.locator(selector).first
                if locator.count() > 0 and locator.is_visible(timeout=1000):
                    locator.click(timeout=3000)

    def _skip_if_antibot_detected(self) -> None:
        title = self.page.title().lower()
        text = self.page.locator("body").inner_text(timeout=3000).lower()
        antibot_markers = [
            "access denied",
            "captcha",
            "cloudflare",
            "ddos",
            "verify you are human",
            "проверка, что вы не робот",
            "доступ временно ограничен",
            "подозрительная активность",
        ]
        if any(marker in title or marker in text for marker in antibot_markers):
            pytest.skip(
                "Обнаружена антибот-защита/капча на странице. "
                f"URL='{self.page.url}', title='{self.page.title()}'"
            )

    def safe_click(self, locator: Locator, step_name: str) -> None:
        with allure.step(step_name):
            expect(locator).to_be_visible()
            locator.click()
