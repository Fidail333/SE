from __future__ import annotations

import re

from playwright.sync_api import expect

from .base_page import BasePage


class FootballPage(BasePage):
    def assert_opened(self) -> None:
        expect(self.page).to_have_url(re.compile(r"/football/", re.IGNORECASE))
        heading = self.page.get_by_role("heading").first
        expect(heading).to_be_visible()
        expect(heading).to_contain_text(re.compile(r"футбол", re.IGNORECASE))
