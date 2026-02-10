from __future__ import annotations

import re

import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class SectionPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def assert_section_opened(self, section_name: str) -> None:
        with allure.step(f"Проверить, что раздел '{section_name}' открыт"):
            expect(self.page.locator("main")).to_be_visible()
            heading = self.page.get_by_role("heading").first
            if heading.count() > 0:
                expect(heading).to_contain_text(re.compile(re.escape(section_name), re.IGNORECASE))

    def open_first_material_in_section(self) -> None:
        with allure.step("Открыть первый материал раздела"):
            link = self.page.locator("main a[href*='/news/'], main article a[href]").first
            expect(link).to_be_visible()
            link.click()
