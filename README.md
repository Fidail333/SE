# SE Desktop + URL Health Autotests (Pytest + Playwright + Requests + Allure)

Автотесты для **sport-express.ru** состоят из двух независимых слоев:

- `desktop` слой: стабильная UI-матрица по всем URL из `data/urls.py::URL_CASES`.
- `http` слой: HTTP/HTML health checks по тем же URL.

Основной desktop-набор рассчитан на запуск с whitelisted IP.

## Что проверяется

### Desktop UI (`@pytest.mark.desktop`)

- Для каждого URL выполняется прямой `goto`.
- Проверяется отсутствие антибота/капчи (fail-fast, без `skip`).
- Проверяется базовая desktop-структура страницы.
- Проверяется профиль страницы по rule-based модели (`home/section/listing`, `article-like`, `stats/live`, `service`).
- В Allure формируются русские шаги и артефакты навигации.

### HTTP Health (`@pytest.mark.http`)

- Разрешены редиректы `301/302/307/308`, но финальный ответ должен быть `200`.
- Запрещены любые `5xx`.
- `Content-Type` должен содержать `text/html` или `application/xhtml+xml` (кроме спец-правил).
- HTML должен быть непустым (по умолчанию `len(body) > 2000`).
- Обязательны `<html`, `<body` и непустой `<title>` (кроме спец-правил).
- Негативный URL `https://www.sport-express.ru/asdasdasd/` должен вернуть `404` или `410`.

## Марки

- `@pytest.mark.desktop` — desktop UI матрица по `URL_CASES`.
- `@pytest.mark.http` — HTTP health checks.
- `@pytest.mark.smoke` — быстрый набор (первые `SMOKE_URLS_COUNT` URL + негативный HTTP кейс).
- `@pytest.mark.regression` — полный набор.
- `@pytest.mark.legacy` — исторические UI suites, оставлены в `skip`.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

python -m pip install --upgrade pip
pip install -e .[dev]
python -m playwright install chromium
```

## Локальный запуск

Все тесты:

```bash
python -m pytest
```

Desktop smoke:

```bash
python -m pytest -m "desktop and smoke"
```

Desktop regression:

```bash
python -m pytest -m "desktop and regression"
```

HTTP smoke:

```bash
python -m pytest -m "http and smoke"
```

HTTP regression:

```bash
python -m pytest -m "http and regression"
```

Legacy наборы (по умолчанию `skip`):

```bash
python -m pytest -m legacy -rs
```

## Проверка переноса русских шагов в TestOps

После прогона через `allurectl watch` проверьте результаты:

```bash
python scripts/validate_allure_results.py --mode smoke --results-dir allure-results
python scripts/validate_allure_results.py --mode regression --results-dir allure-results
```

Скрипт валидирует:

- ожидаемое количество desktop-кейсов;
- отсутствие `skipped` в desktop-наборе;
- наличие `steps` в каждом desktop-кейсе;
- наличие кириллицы минимум в одном шаге каждого desktop-кейса.

## Allure локально

```bash
python -m pytest --alluredir=allure-results
allure serve allure-results
```
