from __future__ import annotations

import re

import allure
from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage


class MaterialPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

    @property
    def title(self) -> Locator:
        return self.page.get_by_role("heading", level=1).first

    @property
    def publish_date(self) -> Locator:
        return self.page.locator("time, [datetime]").first

    @property
    def author(self) -> Locator:
        return self.page.locator("[rel='author'], [itemprop='author'], .author, a[href*='/authors/']").first

    @property
    def content_blocks(self) -> Locator:
        return self.page.locator("article p, .article p, [itemprop='articleBody'] p")

    @property
    def breadcrumbs(self) -> Locator:
        return self.page.locator("nav[aria-label*='breadcrumb' i], .breadcrumb, .breadcrumbs")

    @property
    def tags(self) -> Locator:
        return self.page.locator("a[href*='/tags/'], .tags a")

    def assert_material_basics(self) -> None:
        with allure.step("Проверить базовые элементы материала"):
            expect(self.title).to_be_visible()
            expect(self.title).not_to_be_empty()
            expect(self.publish_date).to_be_visible()
            expect(self.content_blocks.first).to_be_visible()

    def assert_breadcrumbs_if_present(self) -> None:
        with allure.step("Проверить хлебные крошки (если есть)"):
            if self.breadcrumbs.count() > 0:
                expect(self.breadcrumbs.first).to_be_visible()

    def assert_tags_or_category_if_present(self) -> None:
        with allure.step("Проверить теги/категории (если есть)"):
            if self.tags.count() > 0:
                expect(self.tags.first).to_be_visible()

    def assert_author_if_present(self) -> None:
        with allure.step("Проверить автора (если есть)"):
            if self.author.count() > 0:
                expect(self.author).to_be_visible()

    def assert_material_url(self) -> None:
        with allure.step("Проверить, что открыт URL материала"):
            expect(self.page).to_have_url(re.compile(r"/(news|football|hockey|basketball|tennis)/", re.IGNORECASE))
