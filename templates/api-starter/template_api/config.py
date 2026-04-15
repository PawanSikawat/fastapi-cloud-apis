from functools import lru_cache

from shared.config import SharedSettings


class Settings(SharedSettings):
    cookie_secret_key: str = "dev-secret-change-in-production"
    app_name: str = "Starter API"
    app_description: str = "Rename this starter and replace the example endpoint."


@lru_cache
def get_settings() -> Settings:
    return Settings()
