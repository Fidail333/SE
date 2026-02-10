from __future__ import annotations

import allure
import pytest

from data.sections import EXTRA_SECTIONS, MAIN_SECTIONS
from pages.home_page import HomePage
from pages.material_page import MaterialPage
from pages.section_page import SectionPage


@allure.epic("СЭ UI")
@allure.feature("Materials")
@allure.story("Валидация страниц материалов")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("section_name", MAIN_SECTIONS + EXTRA_SECTIONS)
@allure.title("Материал из раздела '{section_name}' содержит базовые атрибуты")
def test_material_has_required_fields(page, section_name: str):
    home = HomePage(page)
    section = SectionPage(page)
    material = MaterialPage(page)

    home.open()
    home.open_section_from_menu(section_name)
    section.open_first_material_in_section()

    material.assert_material_basics()
    material.assert_author_if_present()
    material.assert_tags_or_category_if_present()


@allure.epic("СЭ UI")
@allure.feature("Materials")
@allure.story("Навигация материала")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("section_name", ["Футбол", "Хоккей", "Теннис"])
@allure.title("Материал содержит корректные хлебные крошки: раздел {section_name}")
def test_material_breadcrumbs(page, section_name: str):
    home = HomePage(page)
    section = SectionPage(page)
    material = MaterialPage(page)

    home.open()
    home.open_section_from_menu(section_name)
    section.open_first_material_in_section()

    material.assert_material_url()
    material.assert_breadcrumbs_if_present()
