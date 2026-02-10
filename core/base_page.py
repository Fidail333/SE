from __future__ import annotations

from urllib.parse import urljoin

import allure
from playwright.sync_api import Locator, Page, expect

from core.config import get_settings


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.settings = get_settings()

    def open_path(self, path: str = "/") -> None:
        target = urljoin(f"{self.settings.base_url}/", path.lstrip("/"))
        with allure.step(f"Open URL: {target}"):
            self.page.goto(target, wait_until="domcontentloaded")

    def wait_ready(self) -> None:
        expect(self.page.locator("body")).to_be_visible()

    def safe_click(self, locator: Locator, step_name: str) -> None:
        with allure.step(step_name):
            expect(locator).to_be_visible()
            locator.click()
