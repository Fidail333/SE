from __future__ import annotations

import json
from pathlib import Path

import allure
import pytest
from allure_commons.types import AttachmentType
from playwright.sync_api import Page

from core.allure_helpers import attach_page_source, attach_screenshot
from fixtures.browser import *  # noqa: F403
from utils.retries import is_transient_error


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or report.passed:
        return

    page: Page | None = item.funcargs.get("page")  # type: ignore[assignment]
    if not page:
        return

    attach_screenshot(page, name="failure-screenshot")
    attach_page_source(page, name="failure-page-source")

    console_messages = getattr(page, "console_messages", [])
    allure.attach(
        "\n".join(console_messages) if console_messages else "No console messages",
        name="browser-console.log",
        attachment_type=AttachmentType.TEXT,
    )

    request_failures = getattr(page, "request_failures", [])
    allure.attach(
        json.dumps(request_failures, ensure_ascii=False, indent=2),
        name="network-failures.json",
        attachment_type=AttachmentType.JSON,
    )


@pytest.hookimpl(tryfirst=True)
def pytest_exception_interact(node: pytest.Item, call: pytest.CallInfo[None], report: pytest.TestReport) -> None:
    if report.failed and call.excinfo and is_transient_error(str(call.excinfo.value)):
        report.wasxfail = "Transient UI issue detected; consider rerun."


@pytest.fixture(scope="session", autouse=True)
def ensure_allure_results_dir() -> None:
    Path("allure-results").mkdir(parents=True, exist_ok=True)
