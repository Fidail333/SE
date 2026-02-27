.PHONY: install test smoke regression desktop-smoke desktop-regression http-smoke http-regression allure

install:
	python -m pip install -U pip
	pip install -e .[dev]
	python -m playwright install chromium

test:
	python -m pytest

smoke:
	python -m pytest -m "desktop and smoke"

regression:
	python -m pytest -m "desktop and regression"

desktop-smoke:
	python -m pytest -m "desktop and smoke"

desktop-regression:
	python -m pytest -m "desktop and regression"

http-smoke:
	python -m pytest -m "http and smoke"

http-regression:
	python -m pytest -m "http and regression"

allure:
	allure serve allure-results
