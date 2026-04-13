from functools import lru_cache

from shared.config import SharedSettings


class Settings(SharedSettings):
    browser_pool_size: int = 3
    render_timeout: float = 30.0
    max_content_size: int = 5_242_880
    default_format: str = "A4"
    default_orientation: str = "portrait"
    default_margin_top: str = "20mm"
    default_margin_right: str = "20mm"
    default_margin_bottom: str = "20mm"
    default_margin_left: str = "20mm"
    default_scale: float = 1.0
    default_print_background: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
