from __future__ import annotations

import re

import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class ErrorPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def open_missing_page(self) -> None:
        with allure.step("Открыть несуществующую страницу"):
            self.open_path("/this-page-should-not-exist-qa-automation")

    def assert_not_found(self) -> None:
        with allure.step("Проверить отображение 404"):
            body = self.page.locator("body")
            expect(body).to_be_visible()
            expect(body).to_contain_text(re.compile("404|не найдена|not found", re.IGNORECASE))
