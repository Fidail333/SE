from __future__ import annotations

import re

import allure
from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage


class SearchPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

    @property
    def results_links(self) -> Locator:
        return self.page.locator("main a[href]")

    @property
    def no_results_text(self) -> Locator:
        return self.page.locator("main").get_by_text(
            re.compile("ничего не найдено|нет результатов|по вашему запросу", re.IGNORECASE)
        )

    def assert_results_visible(self, query: str) -> None:
        with allure.step("Проверить, что отобразились результаты поиска"):
            expect(self.page).to_have_url(re.compile("search|q=|query=", re.IGNORECASE))
            expect(self.page.locator("main")).to_be_visible()
            expect(self.results_links.first).to_be_visible()
            if query.lower() not in self.page.url.lower():
                heading = self.page.get_by_role("heading").first
                expect(heading).to_contain_text(re.compile(re.escape(query), re.IGNORECASE))

    def open_first_result(self) -> None:
        with allure.step("Открыть первый результат поиска"):
            expect(self.results_links.first).to_be_visible()
            self.results_links.first.click()

    def assert_empty_or_no_results_state(self) -> None:
        with allure.step("Проверить корректную обработку пустого/некорректного поиска"):
            expect(self.page.locator("main")).to_be_visible()
            has_no_results = self.no_results_text.count() > 0
            has_results = self.results_links.count() > 0
            assert has_no_results or has_results
