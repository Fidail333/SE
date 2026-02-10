import pytest
from playwright.sync_api import BrowserContext, Page


@pytest.fixture
def page_with_viewport(context: BrowserContext) -> Page:
    page = context.new_page()
    page.set_viewport_size({"width": 1440, "height": 900})
    return page
