from functools import lru_cache

from shared.config import SharedSettings


class Settings(SharedSettings):
    cache_ttl: int = 86400
    max_logo_size: int = 512_000
    max_data_length: int = 2953
    cookie_secret_key: str = "dev-secret-change-in-production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
