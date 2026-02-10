from __future__ import annotations

import json
from urllib.parse import urlparse

import allure
import pytest

from data.urls import NEGATIVE_URL, SMOKE_URLS_COUNT, URL_CASES
from utils.http_health import assert_positive_html_health, request_with_retry


pytestmark = pytest.mark.regression


def _case_id(url: str) -> str:
    parsed = urlparse(url)
    value = (parsed.path or "/").strip("/")
    if parsed.query:
        value = f"{value}?{parsed.query}" if value else f"?{parsed.query}"
    return value or "home"


def _attach_response_artifacts(url: str, status: int, final_url: str, headers: dict[str, str], body: str) -> None:
    allure.attach(final_url, name="final_url", attachment_type=allure.attachment_type.TEXT)
    allure.attach(str(status), name="status", attachment_type=allure.attachment_type.TEXT)
    allure.attach(
        json.dumps(headers, ensure_ascii=False, indent=2),
        name="headers",
        attachment_type=allure.attachment_type.JSON,
    )
    allure.attach(body, name="html", attachment_type=allure.attachment_type.HTML)


URL_PARAMS = [
    pytest.param(
        url,
        marks=[pytest.mark.smoke] if index < SMOKE_URLS_COUNT else [],
        id=f"url:{_case_id(url)}",
    )
    for index, url in enumerate(URL_CASES)
]


@allure.epic("SE URL Health")
@allure.feature("HTTP/HTML checks")
@pytest.mark.parametrize("url", URL_PARAMS)
def test_url_health(url: str) -> None:
    allure.dynamic.title(f"URL health: {_case_id(url)}")
    response = request_with_retry(url)

    _attach_response_artifacts(
        url=url,
        status=response.status_code,
        final_url=response.final_url,
        headers=response.headers,
        body=response.body,
    )

    assert_positive_html_health(response)


@allure.epic("SE URL Health")
@allure.feature("HTTP negative checks")
@pytest.mark.smoke
@allure.title("Negative URL returns 404/410")
def test_negative_url_health() -> None:
    response = request_with_retry(NEGATIVE_URL)
    _attach_response_artifacts(
        url=NEGATIVE_URL,
        status=response.status_code,
        final_url=response.final_url,
        headers=response.headers,
        body=response.body,
    )

    assert response.status_code in {404, 410}, f"Expected 404/410, got {response.status_code}"
