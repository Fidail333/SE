from __future__ import annotations

import re

from playwright.sync_api import Locator, expect

from .base_page import BasePage


class HomePage(BasePage):
    URL = "https://www.sport-express.ru/"

    @property
    def header(self) -> Locator:
        return self.page.get_by_role("banner")

    @property
    def logo(self) -> Locator:
        return self.page.locator("header a[aria-label], header a").filter(
            has_text=re.compile(r"спорт-экспресс|sport-express", re.IGNORECASE)
        ).first

    @property
    def search_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"поиск|search", re.IGNORECASE)).first

    @property
    def search_input(self) -> Locator:
        return self.page.get_by_role("searchbox").first

    @property
    def football_link(self) -> Locator:
        return self.page.get_by_role("link", name=re.compile(r"^футбол$", re.IGNORECASE)).first

    @property
    def footer(self) -> Locator:
        return self.page.get_by_role("contentinfo")

    def open(self) -> None:
        self.goto(self.URL)
        self.wait_for_ready()

    def assert_header_and_logo_visible(self) -> None:
        expect(self.header).to_be_visible()
        # Some layouts may not expose logo text as link name. Fallback to image alt text.
        logo_by_img_alt = self.page.get_by_alt_text(
            re.compile(r"спорт-экспресс|sport-express", re.IGNORECASE)
        ).first

        if self.logo.count() > 0:
            expect(self.logo).to_be_visible()
        else:
            expect(logo_by_img_alt).to_be_visible()

    def open_search_and_type(self, query: str) -> None:
        if self.search_button.count() > 0:
            self.search_button.click()

        expect(self.search_input).to_be_visible()
        self.search_input.fill(query)
        self.search_input.press("Enter")

    def open_football_section(self) -> None:
        expect(self.football_link).to_be_visible()
        self.football_link.click()

    def open_first_news_article(self) -> None:
        news_link = self.page.locator(
            "a[href*='/news/']"
        ).filter(has_not_text=re.compile(r"реклама", re.IGNORECASE)).first
        expect(news_link).to_be_visible()
        news_link.click()

    def assert_footer_visible(self) -> None:
        expect(self.footer).to_be_visible()
