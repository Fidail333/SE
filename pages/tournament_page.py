from __future__ import annotations

import re

import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class TournamentPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def open_by_path(self, path: str) -> None:
        with allure.step(f"Открыть турнирную/матчевую страницу: {path}"):
            self.open_path(path)
            self.wait_ready()

    def assert_basic_elements(self) -> None:
        with allure.step("Проверить базовые элементы страницы турнира/матча"):
            expect(self.page.locator("main")).to_be_visible()
            heading = self.page.get_by_role("heading").first
            expect(heading).to_be_visible()
            expect(heading).not_to_be_empty()

    def assert_related_keyword(self, keyword: str) -> None:
        with allure.step(f"Проверить наличие ключевого слова '{keyword}'"):
            expect(self.page.locator("body")).to_contain_text(re.compile(re.escape(keyword), re.IGNORECASE))
