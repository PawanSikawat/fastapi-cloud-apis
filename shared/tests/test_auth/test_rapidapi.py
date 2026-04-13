import pytest
from fastapi import HTTPException
from starlette.requests import Request

from shared.auth.rapidapi import validate_rapidapi


def _make_request(headers: dict[str, str]) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope)


class TestValidateRapidapi:
    @pytest.mark.asyncio
    async def test_valid_proxy_secret(self) -> None:
        request = _make_request(
            {
                "x-rapidapi-proxy-secret": "secret123",
                "x-rapidapi-user": "user456",
                "x-rapidapi-subscription": "PRO",
            }
        )
        info = await validate_rapidapi(request, expected_secret="secret123")
        assert info["channel"] == "rapidapi"
        assert info["plan"] == "basic"  # PRO maps to basic
        assert info["is_active"] is True

    @pytest.mark.asyncio
    async def test_invalid_proxy_secret_raises_401(self) -> None:
        request = _make_request({"x-rapidapi-proxy-secret": "wrong"})
        with pytest.raises(HTTPException) as exc_info:
            await validate_rapidapi(request, expected_secret="secret123")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_subscription_defaults_to_free(self) -> None:
        request = _make_request(
            {
                "x-rapidapi-proxy-secret": "secret123",
                "x-rapidapi-user": "user789",
            }
        )
        info = await validate_rapidapi(request, expected_secret="secret123")
        assert info["plan"] == "free"
