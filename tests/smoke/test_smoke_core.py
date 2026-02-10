from __future__ import annotations

import allure
import pytest

pytestmark = pytest.mark.skip(reason="replaced by URL health checks")


from data.sections import MAIN_SECTIONS
from pages.home_page import HomePage
from pages.material_page import MaterialPage
from pages.search_page import SearchPage
from pages.section_page import SectionPage


@allure.epic("СЭ UI")
@allure.feature("Smoke")
@pytest.mark.ui
@pytest.mark.smoke
@allure.title("Главная страница успешно открывается и содержит ключевые блоки")
def test_homepage_core_blocks(page):
    home = HomePage(page)
    home.open()
    home.assert_key_blocks_visible()


@allure.epic("СЭ UI")
@allure.feature("Smoke")
@allure.story("Навигация по ключевым разделам")
@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.parametrize("section_name", MAIN_SECTIONS)
@allure.title("Переход в основной раздел: {section_name}")
def test_main_menu_navigation(page, section_name: str):
    home = HomePage(page)
    section = SectionPage(page)

    home.open()
    home.open_section_from_menu(section_name)
    section.assert_section_opened(section_name)


@allure.epic("СЭ UI")
@allure.feature("Smoke")
@allure.story("Поиск")
@pytest.mark.ui
@pytest.mark.smoke
@allure.title("Поиск по популярному запросу возвращает результаты")
def test_search_returns_results(page):
    home = HomePage(page)
    search = SearchPage(page)

    home.open()
    home.search("Спартак")
    search.assert_results_visible("Спартак")


@allure.epic("СЭ UI")
@allure.feature("Smoke")
@allure.story("Материалы")
@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.flaky(reruns=1, reruns_delay=1)
@allure.title("Открытие первого материала из поиска")
def test_open_material_from_search(page):
    home = HomePage(page)
    search = SearchPage(page)
    material = MaterialPage(page)

    home.open()
    home.search("Зенит")
    search.assert_results_visible("Зенит")
    search.open_first_result()

    material.assert_material_url()
    material.assert_material_basics()


@allure.epic("СЭ UI")
@allure.feature("Smoke")
@allure.story("Материалы")
@pytest.mark.ui
@pytest.mark.smoke
@allure.title("Открытие первого материала с главной")
def test_open_material_from_home(page):
    home = HomePage(page)
    material = MaterialPage(page)

    home.open()
    home.open_first_material_from_home()
    material.assert_material_basics()
