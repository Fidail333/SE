from __future__ import annotations

import re

import allure
from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage


class HomePage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

    @property
    def header(self) -> Locator:
        return self.page.get_by_role("banner")

    @property
    def footer(self) -> Locator:
        return self.page.get_by_role("contentinfo")

    @property
    def main_content(self) -> Locator:
        return self.page.locator("main").first

    @property
    def top_news_block(self) -> Locator:
        return self.page.locator("main a[href*='/news/']").first

    @property
    def search_input(self) -> Locator:
        return self.page.get_by_role("searchbox").first

    def open(self) -> None:
        with allure.step("Открыть главную страницу СЭ"):
            self.open_path("/")
            self.wait_ready()
            expect(self.header).to_be_visible()

    def assert_key_blocks_visible(self) -> None:
        with allure.step("Проверить ключевые блоки главной страницы"):
            expect(self.header).to_be_visible()
            expect(self.main_content).to_be_visible()
            expect(self.footer).to_be_visible()
            expect(self.top_news_block).to_be_visible()

    def open_section_from_menu(self, section_name: str) -> None:
        with allure.step(f"Перейти в раздел '{section_name}' из меню"):
            section_link = self.page.get_by_role(
                "link",
                name=re.compile(fr"^{re.escape(section_name)}$", re.IGNORECASE),
            ).first
            if section_link.count() == 0:
                section_link = self.page.locator("header nav a", has_text=section_name).first
            expect(section_link).to_be_visible()
            section_link.click()

    def search(self, query: str) -> None:
        with allure.step(f"Выполнить поиск по запросу: '{query}'"):
            toggle = self.page.get_by_role("button", name=re.compile("поиск|search", re.IGNORECASE)).first
            if toggle.count() > 0:
                toggle.click()
            expect(self.search_input).to_be_visible()
            self.search_input.fill(query)
            self.search_input.press("Enter")

    def open_first_material_from_home(self) -> None:
        with allure.step("Открыть первый материал из ленты на главной"):
            candidates = self.page.locator(
                "main a[href*='/news/'], main a[href*='/football/'], main a[href*='/hockey/']"
            )
            expect(candidates.first).to_be_visible()
            candidates.first.click()
