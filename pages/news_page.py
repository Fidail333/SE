from __future__ import annotations

import re

from playwright.sync_api import expect

from .base_page import BasePage


class NewsPage(BasePage):
    def assert_opened(self) -> None:
        expect(self.page).to_have_url(re.compile(r"/news/", re.IGNORECASE))
        headline = self.page.get_by_role("heading", level=1).first
        expect(headline).to_be_visible()
        expect(headline).not_to_be_empty()
