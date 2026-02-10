# Автотесты для sport-express.ru (Python + pytest-playwright)

Проект использует **Page Object Model**:
- `pages/` — page objects
- `tests/` — E2E/UI smoke-тесты

## Что проверяется

1. Главная страница открывается, есть header/логотип.
2. Поиск: открыть поиск, ввести `Зенит`, убедиться, что есть страница/результаты.
3. Раздел `Футбол` открывается.
4. Открывается страница новости (берётся первая доступная ссылка новости на главной).
5. На главной есть footer.

Тесты сделаны без привязки к конкретным новостям и используют устойчивые локаторы (role/aria/text + URL-паттерны).

## Установка (Windows через WSL)

```bash
# WSL (Ubuntu)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Запуск тестов

```bash
# Базовый запуск
pytest -s -v --browser chromium

# В headed-режиме
pytest -s -v --browser chromium --headed

# С замедлением действий (slowmo)
pytest -s -v --browser chromium --headed --slowmo 250
```

## Примечания

- Используются ожидания Playwright (`expect(...)`) по состоянию элементов/URL.
- `sleep` не используется.
- Запросы к сайту сведены к минимуму (smoke-набор, без лишних переходов).
