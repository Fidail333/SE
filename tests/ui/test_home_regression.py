from __future__ import annotations

import allure
import pytest

pytestmark = pytest.mark.skip(reason="replaced by URL health checks")


from data.sections import EXTRA_SECTIONS, MAIN_SECTIONS
from pages.home_page import HomePage
from pages.section_page import SectionPage


@allure.epic("СЭ UI")
@allure.feature("Home")
@allure.story("Навигация")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("section_name", MAIN_SECTIONS + EXTRA_SECTIONS)
@allure.title("Навигация с главной в раздел '{section_name}'")
def test_navigation_from_home(page, section_name: str):
    home = HomePage(page)
    section = SectionPage(page)

    home.open()
    home.open_section_from_menu(section_name)
    section.assert_section_opened(section_name)


@allure.epic("СЭ UI")
@allure.feature("Home")
@allure.story("Контент")
@pytest.mark.ui
@pytest.mark.regression
@allure.title("Главная содержит ленту материалов")
def test_home_has_material_feed(page):
    home = HomePage(page)

    home.open()
    assert home.page.locator("main a[href]").count() > 5
