from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class SharedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    database_url: str
    redis_url: str
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    rapidapi_proxy_secret: str = ""


@lru_cache
def get_shared_settings() -> SharedSettings:
    return SharedSettings()
