# SE Desktop + URL Health Autotests (Pytest + Playwright + Requests + Allure)

Автотесты для **sport-express.ru** состоят из двух независимых слоев:

- `desktop` слой: стабильная UI-матрица по всем URL из `data/urls.py::URL_CASES`.
- `http` слой: HTTP/HTML health checks по тем же URL.

Основной desktop-набор рассчитан на запуск с whitelisted IP.

## Базовые окружения (`BASE_URL`)

- Прод по умолчанию: `https://www.sport-express.ru/`
- Локальное окружение: `http://www.sport-express.env0/`
- Локальное окружение: `http://www.sport-express.env3/`

Если `BASE_URL` не задан, используется прод `https://www.sport-express.ru/`.

## Запуск локально (для новичка)

Ниже самый простой путь для `macOS/Linux`, если запускаете проект впервые.

### 1) Склонировать проект

```bash
git clone <URL_репозитория>
cd SE
```

### 2) Проверить, что есть Python 3.11+

```bash
python3 --version
```

Если команда не найдена, установите Python 3 и повторите.

### 3) Создать виртуальное окружение и установить зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[dev]
python -m playwright install chromium
```

### 4) Запустить тесты на `env0`

```bash
rm -rf allure-results
JS_HEALTH_MODE=warn HEADLESS=true TEST_ENV=env0 BASE_URL=http://www.sport-express.env0 python -m pytest -m "desktop and regression" --alluredir=allure-results
```

Если хотите видеть браузер во время прогона:

```bash
JS_HEALTH_MODE=warn HEADLESS=false TEST_ENV=env0 BASE_URL=http://www.sport-express.env0 python -m pytest -m "desktop and regression" --alluredir=allure-results
```

### 5) Открыть Allure-отчёт

Если `allure` не установлен в системе, можно использовать локальный бинарник:

```bash
curl -L -o allure.tgz https://github.com/allure-framework/allure2/releases/download/2.29.0/allure-2.29.0.tgz
tar -xzf allure.tgz
./allure-2.29.0/bin/allure serve allure-results
```

Если `allure` уже установлен глобально, достаточно:

```bash
allure serve allure-results
```

### 6) (Опционально) Отправить результаты в TestOps

Локальный `pytest --alluredir=...` сохраняет результаты только на вашей машине.  
Для отправки в TestOps используйте `allurectl watch`:

```bash
ALLURE_ENDPOINT=https://testops.sport-express.ru \
ALLURE_PROJECT_ID=15 \
ALLURE_TOKEN=<TOKEN> \
ALLURE_RESULTS=allure-results \
TEST_ENV=env0 \
BASE_URL=http://www.sport-express.env0 \
./allurectl watch -- python -m pytest -m "desktop and regression" --alluredir=allure-results
```

## Что проверяется

### Desktop UI (`@pytest.mark.desktop`)

- Для каждого URL выполняется прямой `goto`.
- Проверяется отсутствие антибота/капчи (fail-fast, без `skip`).
- Проверяется базовая desktop-структура страницы.
- Проверяется профиль страницы по rule-based модели (`home/section/listing`, `article-like`, `stats/live`, `service`).
- Проверяются SEO-инварианты (`title`, `canonical`, `meta robots`).
- Проверяются контентные инварианты (пустые/placeholder состояния, минимальная валидность контента).
- Проверяется JS/Network health (console error + requestfailed с allowlist исключениями).
  По умолчанию режим `warning` (`JS_HEALTH_MODE=warn`), строгий фейл-режим: `JS_HEALTH_MODE=strict`.
- Формируется отдельный шаг `Сводка JS/Network`.
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
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

python -m pip install --upgrade pip
pip install -e .[dev]
python -m playwright install chromium
```

## Локальный запуск

Прод (по умолчанию):

```bash
python3 -m pytest --alluredir=allure-results
```

Локально на `env0`:

```bash
BASE_URL=http://www.sport-express.env0 python3 -m pytest --alluredir=allure-results
```

Локально на `env3`:

```bash
BASE_URL=http://www.sport-express.env3 python3 -m pytest --alluredir=allure-results
```

Все тесты:

```bash
python3 -m pytest
```

Desktop smoke:

```bash
python3 -m pytest -m "desktop and smoke"
```

Desktop regression:

```bash
python3 -m pytest -m "desktop and regression"
```

HTTP smoke:

```bash
python3 -m pytest -m "http and smoke"
```

HTTP regression:

```bash
python3 -m pytest -m "http and regression"
```

Legacy наборы (по умолчанию `skip`):

```bash
python3 -m pytest -m legacy -rs
```

## Проверка переноса русских шагов в TestOps

После прогона через `allurectl watch` проверьте результаты:

```bash
python3 scripts/validate_allure_results.py --mode smoke --env env0 --results-dir allure-results
python3 scripts/validate_allure_results.py --mode regression --env env0 --results-dir allure-results
```

Скрипт валидирует:

- ожидаемое количество desktop-кейсов;
- отсутствие `skipped` в desktop-наборе;
- наличие `steps` в каждом desktop-кейсе;
- наличие кириллицы минимум в одном шаге каждого desktop-кейса.
- наличие обязательных step-паков (`Антибот`, `База`, `SEO`, `Content`, `JS`).
- taxonomy падений (`infra/test/product`) и долю `uncategorized`.

## CI матрица сред

- `desktop_smoke_env0`, `desktop_smoke_env3` — blocking smoke на push/MR.
- `desktop_smoke_prod` — наблюдение на schedule/web, `allow_failure=true`.
- `desktop_regression_env0`, `desktop_regression_env3`, `desktop_regression_prod` — regression на schedule/web (prod наблюдательный).
- `http_health` — быстрый отдельный сигнал по HTTP checks.

## Allure локально

```bash
python3 -m pytest --alluredir=allure-results
allure serve allure-results
```
