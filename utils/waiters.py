from __future__ import annotations

import re

from playwright.sync_api import Locator, Page, expect


def expect_url_contains(page: Page, value: str) -> None:
    expect(page).to_have_url(re.compile(re.escape(value), re.IGNORECASE))


def expect_visible(locator: Locator) -> None:
    expect(locator).to_be_visible()


def expect_non_empty_text(locator: Locator) -> None:
    expect(locator).not_to_be_empty()
