import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from email_validation.services.smtp import verify_smtp


def _make_reader(*responses: str) -> AsyncMock:
    """Create a mock StreamReader that returns predefined SMTP responses."""
    reader = AsyncMock(spec=asyncio.StreamReader)
    encoded = [f"{r}\r\n".encode() for r in responses]
    reader.readline = AsyncMock(side_effect=encoded)
    return reader


def _make_writer() -> AsyncMock:
    writer = AsyncMock(spec=asyncio.StreamWriter)
    writer.write = lambda data: None  # type: ignore[assignment]
    writer.drain = AsyncMock()
    writer.close = lambda: None  # type: ignore[assignment]
    return writer


class TestSmtpVerification:
    @pytest.mark.asyncio
    async def test_mailbox_verified(self) -> None:
        reader = _make_reader(
            "220 mail.example.com ESMTP",  # banner
            "250 OK",  # EHLO
            "250 OK",  # MAIL FROM
            "250 OK",  # RCPT TO (real)
            "550 No such user",  # RCPT TO (catch-all probe)
        )
        writer = _make_writer()

        with patch(
            "email_validation.services.smtp.asyncio.open_connection", return_value=(reader, writer)
        ):
            verified, catch_all, reason = await verify_smtp(
                "user@example.com", "mx1.example.com", timeout=5.0
            )
            assert verified is True
            assert catch_all is False

    @pytest.mark.asyncio
    async def test_mailbox_rejected(self) -> None:
        reader = _make_reader(
            "220 mail.example.com ESMTP",
            "250 OK",
            "250 OK",
            "550 No such user",
        )
        writer = _make_writer()

        with patch(
            "email_validation.services.smtp.asyncio.open_connection", return_value=(reader, writer)
        ):
            verified, catch_all, reason = await verify_smtp(
                "bogus@example.com", "mx1.example.com", timeout=5.0
            )
            assert verified is False
            assert catch_all is False

    @pytest.mark.asyncio
    async def test_catch_all_server(self) -> None:
        reader = _make_reader(
            "220 mail.example.com ESMTP",
            "250 OK",
            "250 OK",
            "250 OK",  # RCPT TO (real)
            "250 OK",  # RCPT TO (catch-all probe) — also accepted
        )
        writer = _make_writer()

        with patch(
            "email_validation.services.smtp.asyncio.open_connection", return_value=(reader, writer)
        ):
            verified, catch_all, reason = await verify_smtp(
                "user@example.com", "mx1.example.com", timeout=5.0
            )
            assert verified is None
            assert catch_all is True

    @pytest.mark.asyncio
    async def test_connection_timeout(self) -> None:
        with patch(
            "email_validation.services.smtp.asyncio.open_connection",
            side_effect=TimeoutError(),
        ):
            verified, catch_all, reason = await verify_smtp(
                "user@example.com", "mx1.example.com", timeout=1.0
            )
            assert verified is None
            assert catch_all is None
            assert "timed out" in reason  # type: ignore[operator]

    @pytest.mark.asyncio
    async def test_connection_refused(self) -> None:
        with patch(
            "email_validation.services.smtp.asyncio.open_connection",
            side_effect=OSError("Connection refused"),
        ):
            verified, catch_all, reason = await verify_smtp(
                "user@example.com", "mx1.example.com", timeout=1.0
            )
            assert verified is None
            assert catch_all is None
            assert "Connection refused" in reason  # type: ignore[operator]

    @pytest.mark.asyncio
    async def test_greylisting(self) -> None:
        reader = _make_reader(
            "220 mail.example.com ESMTP",
            "250 OK",
            "250 OK",
            "451 Try again later",
        )
        writer = _make_writer()

        with patch(
            "email_validation.services.smtp.asyncio.open_connection", return_value=(reader, writer)
        ):
            verified, catch_all, reason = await verify_smtp(
                "user@example.com", "mx1.example.com", timeout=5.0
            )
            assert verified is None
            assert "Inconclusive" in reason  # type: ignore[operator]
