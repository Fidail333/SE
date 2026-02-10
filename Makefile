.PHONY: install test smoke regression allure

install:
	python -m pip install -U pip
	pip install -e .[dev]
	python -m playwright install chromium

test:
	python -m pytest

smoke:
	python -m pytest -m smoke

regression:
	python -m pytest -m regression

allure:
	allure serve allure-results
