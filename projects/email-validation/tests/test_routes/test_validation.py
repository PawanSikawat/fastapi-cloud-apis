from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from email_validation.schemas.validation import (
    EmailValidationResponse,
    MxCheck,
    SmtpCheck,
    SyntaxCheck,
    ValidationChecks,
)


def _mock_response(email: str = "user@example.com", **overrides: object) -> EmailValidationResponse:
    defaults = {
        "email": email,
        "result": "deliverable",
        "score": 0.9,
        "is_deliverable": True,
        "is_disposable": False,
        "is_role_based": False,
        "is_free_provider": False,
        "checks": ValidationChecks(
            syntax=SyntaxCheck(valid=True),
            mx=MxCheck(valid=True, records=["mx1.example.com"]),
            smtp=SmtpCheck(verified=True, catch_all=False, reason="Mailbox verified"),
        ),
    }
    defaults.update(overrides)
    return EmailValidationResponse(**defaults)  # type: ignore[arg-type]


class TestValidateSingleEmail:
    @pytest.mark.asyncio
    async def test_valid_email(self, client: AsyncClient) -> None:
        mock_resp = _mock_response()
        with patch(
            "email_validation.routes.validation.validate_email",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            response = await client.post("/v1/validate/email", json={"email": "user@example.com"})
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "user@example.com"
            assert data["result"] == "deliverable"
            assert data["score"] == 0.9
            assert data["is_disposable"] is False

    @pytest.mark.asyncio
    async def test_invalid_email_format(self, client: AsyncClient) -> None:
        response = await client.post("/v1/validate/email", json={"email": "not-an-email"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_email_field(self, client: AsyncClient) -> None:
        response = await client.post("/v1/validate/email", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_disposable_email(self, client: AsyncClient) -> None:
        mock_resp = _mock_response(
            email="user@mailinator.com",
            result="risky",
            score=0.6,
            is_disposable=True,
            is_deliverable=None,
        )
        with patch(
            "email_validation.routes.validation.validate_email",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            response = await client.post(
                "/v1/validate/email", json={"email": "user@mailinator.com"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["is_disposable"] is True
            assert data["result"] == "risky"

    @pytest.mark.asyncio
    async def test_role_based_email(self, client: AsyncClient) -> None:
        mock_resp = _mock_response(
            email="admin@example.com",
            is_role_based=True,
            score=0.8,
        )
        with patch(
            "email_validation.routes.validation.validate_email",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            response = await client.post("/v1/validate/email", json={"email": "admin@example.com"})
            assert response.status_code == 200
            assert response.json()["is_role_based"] is True


class TestValidateBatchEmails:
    @pytest.mark.asyncio
    async def test_batch_validation(self, client: AsyncClient) -> None:
        mock_results = [
            _mock_response(email="a@example.com"),
            _mock_response(email="b@example.com"),
        ]
        with patch(
            "email_validation.routes.validation.validate_emails",
            new_callable=AsyncMock,
            return_value=mock_results,
        ):
            response = await client.post(
                "/v1/validate/email/batch",
                json={"emails": ["a@example.com", "b@example.com"]},
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 2

    @pytest.mark.asyncio
    async def test_batch_exceeds_limit(self, client: AsyncClient) -> None:
        emails = [f"user{i}@example.com" for i in range(51)]
        response = await client.post("/v1/validate/email/batch", json={"emails": emails})
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "BATCH_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_batch_empty_list(self, client: AsyncClient) -> None:
        with patch(
            "email_validation.routes.validation.validate_emails",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = await client.post("/v1/validate/email/batch", json={"emails": []})
            assert response.status_code == 200
            assert response.json()["results"] == []


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
