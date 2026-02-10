# SE URL Health Autotests (Pytest + Requests + Allure)

Стабильные автотесты для **sport-express.ru**. Основная проверка построена на HTTP/HTML health checks по фиксированному списку URL (без flaky UI-ожиданий `networkidle`).

## Что проверяется

- Разрешены редиректы `301/302/307/308`, но финальный ответ должен быть `200`.
- Запрещены любые `5xx`.
- `Content-Type` должен содержать `text/html` или `application/xhtml+xml`.
- HTML должен быть непустым (`len(body) > 2000`).
- Обязательны `<html`, `<body` и непустой `<title>`.
- Негативный URL `https://www.sport-express.ru/asdasdasd/` должен вернуть `404` или `410`.

Все кейсы сохраняют в Allure артефакты: `final_url`, `status`, `headers`, `html`.

## Марки

- `@pytest.mark.regression` — весь набор URL health checks.
- `@pytest.mark.smoke` — топ-10 URL + негативный кейс.
- Старые UI-тесты помечены `skip(reason="replaced by URL health checks")`.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

python -m pip install --upgrade pip
pip install -e .[dev]
```

## Локальный запуск

Запуск всего набора:

```bash
python -m pytest
```

Только smoke:

```bash
python -m pytest -m smoke
```

Только regression:

```bash
python -m pytest -m regression
```

## Allure локально

```bash
python -m pytest --alluredir=allure-results
allure serve allure-results
```

Статический отчёт:

```bash
allure generate allure-results -o allure-report --clean
```
