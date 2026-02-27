from __future__ import annotations

from urllib.parse import urlparse

import allure
import pytest

from data.urls import SMOKE_URLS_COUNT, URL_CASES
from pages.base_page import BasePage
from utils.ui_desktop_health import (
    assert_base_desktop_structure,
    assert_no_antibot,
    assert_profile_structure,
    attach_rule_payload,
    resolve_rule_for_url,
)

pytestmark = [pytest.mark.desktop, pytest.mark.regression]


def _case_id(url: str) -> str:
    parsed = urlparse(url)
    value = (parsed.path or "/").strip("/")
    if parsed.query:
        value = f"{value}?{parsed.query}" if value else f"?{parsed.query}"
    return value or "home"


URL_PARAMS = [
    pytest.param(
        url,
        marks=[pytest.mark.smoke] if index < SMOKE_URLS_COUNT else [],
        id=f"desktop:{_case_id(url)}",
    )
    for index, url in enumerate(URL_CASES)
]


@allure.epic("СЭ Desktop UI")
@allure.feature("Матрица URL")
@pytest.mark.parametrize("url", URL_PARAMS)
def test_desktop_url_matrix(page, url: str) -> None:
    base = BasePage(page)
    resolved = resolve_rule_for_url(url)
    allure.dynamic.title(f"Desktop UI проверка: {_case_id(url)}")
    allure.dynamic.label("desktop_profile", resolved.rule.profile)
    attach_rule_payload(url=url, resolved=resolved)

    with allure.step(f"Открыть страницу: {url}"):
        base.open_path(url)

    with allure.step("Проверить отсутствие антибота/капчи"):
        assert_no_antibot(page)

    with allure.step("Проверить базовую desktop-структуру"):
        assert_base_desktop_structure(page)

    with allure.step(f"Проверить профиль страницы: {resolved.rule.profile}"):
        assert_profile_structure(page=page, resolved=resolved)
