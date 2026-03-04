from __future__ import annotations

import hashlib
import os
import re
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


def _case_title(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    query = f"?{parsed.query}" if parsed.query else ""

    if path == "/":
        return "главная страница (/)"

    normalized_path = path if path.endswith("/") else f"{path}/"
    return f"{normalized_path}{query}"


def _slugify_case_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    if not normalized:
        normalized = "home"
    normalized = normalized[:80].rstrip("_")
    short_hash = hashlib.md5(value.encode("utf-8")).hexdigest()[:8]
    return f"{normalized}_{short_hash}"


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


def _run_desktop_url_case(page, url: str) -> None:
    base = BasePage(page)
    resolved = resolve_rule_for_url(url)
    allure.dynamic.title(f"Проверка десктопного UI: {_case_title(url)}")
    allure.dynamic.label("url_case", _case_id(url))
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

    with allure.step("Проверить базовую десктоп-структуру"):
        assert_base_desktop_structure(page)

    with allure.step(f"Проверить профиль страницы: {resolved.rule.profile}"):
        assert_profile_structure(page=page, resolved=resolved)

    with allure.step("Проверить SEO-инварианты"):
        assert_seo_invariants(page=page, resolved=resolved)

    with allure.step("Проверить контентные инварианты"):
        assert_content_invariants(page=page, resolved=resolved)

    with allure.step("Сводка JS/сети"):
        context_data = attach_js_network_summary(page)

    with allure.step("Проверить состояние JS/сети"):
        assert_js_health(page=page, resolved=resolved, context_data=context_data)


def _build_desktop_test(url: str, index: int):
    case_id = _case_id(url)
    case_title = _case_title(url)
    slug = _slugify_case_id(case_id)
    test_name = f"test_desktop_ui_{index + 1:03d}_{slug}"

    def _test(page, _url: str = url) -> None:
        _run_desktop_url_case(page=page, url=_url)

    _test.__name__ = test_name
    _test.__qualname__ = test_name
    _test.__doc__ = f"Проверка десктопного UI для URL: {case_title}"

    decorated = allure.epic("СЭ Desktop UI")(_test)
    decorated = allure.feature("Матрица URL")(decorated)
    if index < SMOKE_URLS_COUNT:
        decorated = pytest.mark.smoke(decorated)

    return test_name, decorated


for _index, _url in enumerate(URL_CASES):
    _test_name, _test_fn = _build_desktop_test(url=_url, index=_index)
    globals()[_test_name] = _test_fn
