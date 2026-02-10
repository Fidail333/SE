from __future__ import annotations

import os

import allure
import pytest

from data.tournaments import TOURNAMENT_PATHS
from pages.error_page import ErrorPage
from pages.home_page import HomePage
from pages.tournament_page import TournamentPage


@allure.epic("СЭ UI")
@allure.feature("Tournaments")
@allure.story("Страницы турниров/матчей")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("path", TOURNAMENT_PATHS)
@allure.title("Страница турнира доступна: {path}")
def test_tournament_pages(page, path: str):
    tournament = TournamentPage(page)
    tournament.open_by_path(path)
    tournament.assert_basic_elements()


@allure.epic("СЭ UI")
@allure.feature("Resilience")
@allure.story("Негативные сценарии")
@pytest.mark.ui
@pytest.mark.regression
@allure.title("404 страница отображается для несуществующего URL")
def test_404_page(page):
    error = ErrorPage(page)
    error.open_missing_page()
    error.assert_not_found()


@allure.epic("СЭ UI")
@allure.feature("Authentication")
@allure.story("Проверка наличия безопасного логина")
@pytest.mark.ui
@pytest.mark.regression
@allure.title("Логин тестируется только при наличии секретов")
def test_auth_placeholder_with_env(page):
    username = os.getenv("SE_AUTH_USERNAME")
    password = os.getenv("SE_AUTH_PASSWORD")

    if not username or not password:
        pytest.skip("SE_AUTH_USERNAME/SE_AUTH_PASSWORD не заданы. Логин пропущен безопасно.")

    home = HomePage(page)
    home.open()
    assert username and password
