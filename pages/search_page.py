from __future__ import annotations

import re

from playwright.sync_api import expect

from .base_page import BasePage


class SearchPage(BasePage):
    def assert_results_for_query(self, query: str) -> None:
        expect(self.page).to_have_url(re.compile(r"search|q=", re.IGNORECASE))

        results_container = self.page.locator("main").first
        expect(results_container).to_be_visible()

        result_links = self.page.locator("main a[href]")
        expect(result_links.first).to_be_visible()

        # Soft check that query is reflected in URL or heading.
        query_pattern = re.compile(re.escape(query), re.IGNORECASE)
        if query.lower() not in self.page.url.lower():
            heading = self.page.get_by_role("heading").first
            expect(heading).to_contain_text(query_pattern)
