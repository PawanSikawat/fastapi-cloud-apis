from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from email_validation.config import Settings
from email_validation.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(smtp_enabled=False)


@pytest.fixture
def app(settings: Settings) -> None:
    return create_app()


@pytest.fixture
async def client(app: None) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
    ) as ac:
        yield ac
