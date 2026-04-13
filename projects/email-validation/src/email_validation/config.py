from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EMAIL_VALIDATION_")

    smtp_timeout: float = 10.0
    dns_timeout: float = 5.0
    max_batch_size: int = 50
    smtp_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
