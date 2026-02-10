from pages.football_page import FootballPage
from pages.home_page import HomePage
from pages.news_page import NewsPage
from pages.search_page import SearchPage


def test_home_page_opens_and_has_header_logo(page_with_viewport):
    home = HomePage(page_with_viewport)

    home.open()

    home.assert_header_and_logo_visible()


def test_search_zenit_returns_results(page_with_viewport):
    home = HomePage(page_with_viewport)
    search = SearchPage(page_with_viewport)

    home.open()
    home.open_search_and_type("Зенит")

    search.assert_results_for_query("Зенит")


def test_football_section_opens(page_with_viewport):
    home = HomePage(page_with_viewport)
    football = FootballPage(page_with_viewport)

    home.open()
    home.open_football_section()

    football.assert_opened()


def test_news_article_opens_from_home(page_with_viewport):
    home = HomePage(page_with_viewport)
    news = NewsPage(page_with_viewport)

    home.open()
    home.open_first_news_article()

    news.assert_opened()


def test_footer_is_visible_on_home(page_with_viewport):
    home = HomePage(page_with_viewport)

    home.open()

    home.assert_footer_visible()
