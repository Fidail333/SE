from __future__ import annotations

from pathlib import Path

import allure
from allure_commons.types import AttachmentType
from playwright.sync_api import Page


def attach_text(name: str, text: str) -> None:
    allure.attach(text, name=name, attachment_type=AttachmentType.TEXT)


def attach_json(name: str, payload: str) -> None:
    allure.attach(payload, name=name, attachment_type=AttachmentType.JSON)


def attach_file(name: str, file_path: Path, attachment_type: AttachmentType) -> None:
    if file_path.exists():
        allure.attach.file(str(file_path), name=name, attachment_type=attachment_type)


def attach_screenshot(page: Page, name: str = "screenshot") -> None:
    allure.attach(page.screenshot(full_page=True), name=name, attachment_type=AttachmentType.PNG)


def attach_page_source(page: Page, name: str = "page-source") -> None:
    allure.attach(page.content(), name=name, attachment_type=AttachmentType.HTML)
