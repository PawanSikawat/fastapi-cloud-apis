from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class SharedSettings(BaseSettings):
    model_config = SettingsConfigDict()

    database_url: str
    redis_url: str
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    rapidapi_proxy_secret: str = ""
    admin_email: str = "admin@local"
    admin_api_key: str = ""


@lru_cache
def get_shared_settings() -> SharedSettings:
    return SharedSettings()
