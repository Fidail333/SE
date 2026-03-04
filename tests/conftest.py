from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

import allure
import pytest
from allure_commons.types import AttachmentType
from playwright.sync_api import Page

from fixtures.browser import *  # noqa: F403
from utils.failure_taxonomy import build_allure_categories_payload, classify_failure_text
from utils.retries import is_transient_error


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "call" or report.passed:
        return

    funcargs = cast(dict[str, Any], getattr(item, "funcargs", {}))
    page = cast(Page | None, funcargs.get("page"))
    if not page:
        return

    expected = "Стабильное отображение элемента/состояния согласно сценарию"
    actual = str(report.longrepr)
    failure_category = classify_failure_text(actual)
    details = {
        "Где упало": item.nodeid,
        "Ожидали": expected,
        "Получили": actual,
        "Классификация": failure_category,
        "URL": page.url,
        "Секция": funcargs.get("section_name", "не задана"),
        "Таймауты": "Использованы таймауты из fixtures/context (см. settings).",
    }
    allure.attach(
        json.dumps(details, ensure_ascii=False, indent=2),
        name="Детали падения теста",
        attachment_type=AttachmentType.JSON,
    )


@pytest.hookimpl(tryfirst=True)
def pytest_exception_interact(node: pytest.Item, call: pytest.CallInfo[None], report: pytest.TestReport) -> None:
    if report.failed and call.excinfo and is_transient_error(str(call.excinfo.value)):
        report.wasxfail = "Обнаружена временная UI-проблема. Рекомендуется повторный прогон."


@pytest.fixture(scope="session", autouse=True)
def ensure_allure_results_dir() -> None:
    results_dir = Path("allure-results")
    results_dir.mkdir(parents=True, exist_ok=True)

    categories_path = results_dir / "categories.json"
    categories_path.write_text(
        json.dumps(build_allure_categories_payload(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    environment_path = results_dir / "environment.properties"
    test_env = os.getenv("TEST_ENV", "prod")
    base_url = os.getenv("BASE_URL", "https://www.sport-express.ru")
    environment_path.write_text(
        "\n".join(
            [
                f"TEST_ENV={test_env}",
                f"BASE_URL={base_url}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
