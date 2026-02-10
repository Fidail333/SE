from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("BASE_URL", "https://www.sport-express.ru")
    browser: str = os.getenv("BROWSER", "chromium")
    headless: bool = os.getenv("HEADLESS", "true").lower() == "true"
    slowmo_ms: int = int(os.getenv("SLOWMO", "0"))
    default_timeout_ms: int = int(os.getenv("DEFAULT_TIMEOUT", "10000"))
    navigation_timeout_ms: int = int(os.getenv("NAV_TIMEOUT", "25000"))
    retries: int = int(os.getenv("RETRIES", "0"))
    auth_username: str | None = os.getenv("SE_AUTH_USERNAME")
    auth_password: str | None = os.getenv("SE_AUTH_PASSWORD")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
