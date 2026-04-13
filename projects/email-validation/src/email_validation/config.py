from functools import lru_cache

from shared.config import SharedSettings


class Settings(SharedSettings):
    smtp_timeout: float = 10.0
    dns_timeout: float = 5.0
    max_batch_size: int = 50
    smtp_enabled: bool = True
    cookie_secret_key: str = "dev-secret-change-in-production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
