from __future__ import annotations

import json
from urllib.parse import urljoin

import allure
from playwright.sync_api import Locator, Page, expect

from core.config import get_settings
from utils.retries import is_transient_error
from utils.ui_desktop_health import assert_no_antibot, attach_navigation_payload


class BasePage:
    _DEFAULT_PAGE_ANCHOR_SELECTORS = ("header", "nav", "main", "[role='main']", "article", "h1")

    def __init__(self, page: Page) -> None:
        self.page = page
        self.settings = get_settings()

    def open_path(self, path: str = "/") -> None:
        target = urljoin(f"{self.settings.base_url}/", path.lstrip("/"))
        navigation_timeout_ms = max(self.settings.navigation_timeout_ms, 30000)
        total_attempts = max(1, self.settings.retries + 1)

        for attempt in range(1, total_attempts + 1):
            response_status: int | None = None
            try:
                with allure.step(f"Открыть URL: {target} (попытка {attempt}/{total_attempts})"):
                    response = self.page.goto(target, wait_until="domcontentloaded", timeout=navigation_timeout_ms)
                    response_status = response.status if response else None
                    self.page.wait_for_load_state("load", timeout=navigation_timeout_ms)
                    self.wait_for_page_anchor(timeout_ms=navigation_timeout_ms)
                    self._handle_overlays()
                    self._assert_no_antibot_detected()
                    attach_navigation_payload(self.page, requested_url=target, response_status=response_status)
                    return
            except Exception as exc:
                transient = is_transient_error(str(exc))
                self._attach_navigation_error(
                    requested_url=target,
                    attempt=attempt,
                    total_attempts=total_attempts,
                    response_status=response_status,
                    error_text=str(exc),
                    transient=transient,
                )
                if attempt >= total_attempts or not transient:
                    raise

    def _attach_navigation_error(
        self,
        requested_url: str,
        attempt: int,
        total_attempts: int,
        response_status: int | None,
        error_text: str,
        transient: bool,
    ) -> None:
        payload = {
            "requested_url": requested_url,
            "final_url": self.page.url,
            "status_code": response_status,
            "attempt": attempt,
            "total_attempts": total_attempts,
            "transient": transient,
            "error": error_text,
        }
        allure.attach(
            json.dumps(payload, ensure_ascii=False, indent=2),
            name=f"navigation_error_attempt_{attempt}",
            attachment_type=allure.attachment_type.JSON,
        )

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

    def _assert_no_antibot_detected(self) -> None:
        assert_no_antibot(self.page)

    def safe_click(self, locator: Locator, step_name: str) -> None:
        with allure.step(step_name):
            expect(locator).to_be_visible()
            locator.click()
