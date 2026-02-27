from __future__ import annotations

import os
from urllib.parse import urlparse

import allure
import pytest

from data.urls import SMOKE_URLS_COUNT, URL_CASES
from pages.base_page import BasePage
from utils.ui_desktop_health import (
    assert_base_desktop_structure,
    assert_content_invariants,
    assert_js_health,
    assert_no_antibot,
    assert_profile_structure,
    assert_seo_invariants,
    attach_js_network_summary,
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


def _resolve_test_env() -> str:
    explicit = os.getenv("TEST_ENV", "").strip().lower()
    if explicit:
        return explicit

    base_url = os.getenv("BASE_URL", "https://www.sport-express.ru").lower()
    if "env0" in base_url:
        return "env0"
    if "env3" in base_url:
        return "env3"
    return "prod"


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
    allure.dynamic.label("test_env", _resolve_test_env())
    run_id = os.getenv("RUN_ID") or os.getenv("CI_PIPELINE_ID") or ""
    if run_id:
        allure.dynamic.label("run_id", run_id)
    attach_rule_payload(url=url, resolved=resolved)

    with allure.step(f"Открыть страницу: {url}"):
        base.open_path(url)

    with allure.step("Проверить отсутствие антибота/капчи"):
        assert_no_antibot(page)

    with allure.step("Проверить базовую desktop-структуру"):
        assert_base_desktop_structure(page)

    with allure.step(f"Проверить профиль страницы: {resolved.rule.profile}"):
        assert_profile_structure(page=page, resolved=resolved)

    with allure.step("Проверить SEO-инварианты"):
        assert_seo_invariants(page=page, resolved=resolved)

    with allure.step("Проверить контентные инварианты"):
        assert_content_invariants(page=page, resolved=resolved)

    with allure.step("Сводка JS/Network"):
        context_data = attach_js_network_summary(page)

    with allure.step("Проверить JS/Network health"):
        assert_js_health(page=page, resolved=resolved, context_data=context_data)
