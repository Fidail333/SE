from __future__ import annotations

import allure
import pytest

pytestmark = pytest.mark.skip(reason="replaced by URL health checks")


from data.search_queries import INVALID_SEARCH_QUERIES, VALID_SEARCH_QUERIES
from pages.home_page import HomePage
from pages.search_page import SearchPage


@allure.epic("СЭ UI")
@allure.feature("Search")
@allure.story("Позитивные сценарии поиска")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("query", VALID_SEARCH_QUERIES)
@allure.title("Поиск по запросу '{query}' возвращает результаты")
def test_search_positive_queries(page, query: str):
    home = HomePage(page)
    search = SearchPage(page)

    home.open()
    home.search(query)
    search.assert_results_visible(query)


@allure.epic("СЭ UI")
@allure.feature("Search")
@allure.story("Негативные сценарии поиска")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("query", INVALID_SEARCH_QUERIES)
@allure.title("Поиск с запросом '{query}' не ломает страницу")
def test_search_negative_queries(page, query: str):
    home = HomePage(page)
    search = SearchPage(page)

    home.open()
    home.search(query)
    search.assert_empty_or_no_results_state()


@allure.epic("СЭ UI")
@allure.feature("Search")
@allure.story("Переход из поисковой выдачи")
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.flaky(reruns=1, reruns_delay=1)
@allure.title("Переход по первому результату поиска")
def test_open_first_search_result(page):
    home = HomePage(page)
    search = SearchPage(page)

    home.open()
    home.search("КХЛ")
    search.assert_results_visible("КХЛ")
    search.open_first_result()

    assert "sport-express.ru" in page.url
