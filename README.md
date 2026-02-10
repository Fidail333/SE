# SE UI Autotests (Playwright + Pytest + Allure)

Production-grade проект автотестов для **sport-express.ru** (СЭ) с упором на стабильность и масштабируемую архитектуру.

## Стек
- Python 3.11+
- Playwright
- pytest
- allure-pytest
- ruff + mypy + pre-commit

## Архитектура

```text
core/       # config, базовые классы, логирование, allure helpers
fixtures/   # browser/context/page fixtures
pages/      # Page Objects
data/       # тестовые данные
utils/      # wait/retry/attachments utils
tests/
  smoke/    # критичный smoke (8-12)
  regression/
  ui/
```

## Сценарии покрытия

- **Главная**: доступность, ключевые блоки, навигация по разделам.
- **Поиск**: позитивные и негативные запросы, открытие результата.
- **Материалы**: title/date/content, author/tags/breadcrumbs (если есть).
- **Турниры/матчи**: базовая доступность страниц.
- **Негатив**: 404.
- **Авторизация**: безопасный placeholder (только при наличии секретов в env).

Общее покрытие: ~30 тест-кейсов (за счёт параметризации).

## Быстрый старт (Windows 10/11)

### 1) Установить Python 3.11+
Проверьте:

```powershell
python --version
```

### 2) Создать venv и активировать

**PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**cmd:**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3) Установить зависимости

```powershell
python -m pip install --upgrade pip
pip install -e .[dev]
python -m playwright install chromium
```

### 4) Настроить переменные окружения

```powershell
copy .env.example .env
```

Опционально поменяйте `.env`:
- `HEADLESS=false` для визуального прогона
- `SLOWMO=200` для замедления действий
- `BASE_URL` при необходимости

## Запуск тестов

### Одна команда на запуск
```powershell
python -m pytest
```

или через helper:
```powershell
python scripts/run_tests.py
```

### Только smoke
```powershell
python -m pytest -m smoke
```

### Только regression
```powershell
python -m pytest -m regression
```

### Параллельный запуск (опционально)
```powershell
python -m pytest -n 2 -m regression
```

## Allure отчёт

### Генерация/открытие
```powershell
allure serve allure-results
```

Если Allure CLI не установлен:
- через Scoop: `scoop install allure`
- или через Chocolatey: `choco install allure-commandline`

## Стабильность и anti-flaky подход

- Нет `sleep()`; только explicit ожидания Playwright (`expect`).
- Устойчивые локаторы: `role/text` + fallback на CSS.
- Ограниченные ретраи: только на потенциально нестабильных тестах, `reruns=1`.
- Таймауты централизованы в `.env`.
- На падении автоматом прикладываются:
  - screenshot,
  - HTML source,
  - browser console,
  - network failures.

## CI (GitHub Actions)

Workflow `.github/workflows/ci.yml` запускает:
1. ruff
2. mypy
3. smoke-тесты
4. загрузку `allure-results` как artifact

## Troubleshooting

- **`Executable doesn't exist`** → выполните `python -m playwright install chromium`.
- **Тесты падают по UI-изменениям** → обновите локаторы в `pages/` (локаторы вынесены и легко адаптируются).
- **Нет логина в UI / изменился flow** → auth-тест скипается при пустых `SE_AUTH_USERNAME/SE_AUTH_PASSWORD`.

