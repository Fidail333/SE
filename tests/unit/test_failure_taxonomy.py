from __future__ import annotations

from utils.failure_taxonomy import UNCATEGORIZED_KEY, classify_failure_text


def test_classify_infra_failure() -> None:
    message = "AssertionError: Обнаружена антибот-защита/капча. marker='ddos', title='DDoS-Guard'"
    assert classify_failure_text(message) == "infra"


def test_classify_test_failure() -> None:
    message = "AssertionError: Locator expected to be visible"
    assert classify_failure_text(message) == "test"


def test_classify_product_failure() -> None:
    message = "AssertionError: 5xx response: 503"
    assert classify_failure_text(message) == "product"


def test_classify_uncategorized_when_unknown() -> None:
    message = "AssertionError: Totally new unknown failure signature"
    assert classify_failure_text(message) == UNCATEGORIZED_KEY
