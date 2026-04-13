from unittest.mock import AsyncMock, patch

import dns.asyncresolver
import dns.rdatatype
import pytest

from email_validation.services.dns_lookup import check_mx


class TestMxLookup:
    @pytest.mark.asyncio
    async def test_mx_found(self) -> None:
        mock_rdata = type("MockRdata", (), {"preference": 10, "exchange": "mx1.example.com."})()
        mock_answer = [mock_rdata]

        with patch.object(
            dns.asyncresolver.Resolver, "resolve", new_callable=AsyncMock, return_value=mock_answer
        ):
            valid, records = await check_mx("example.com")
            assert valid is True
            assert records == ["mx1.example.com"]

    @pytest.mark.asyncio
    async def test_mx_multiple_records_sorted(self) -> None:
        rdata1 = type("MockRdata", (), {"preference": 20, "exchange": "mx2.example.com."})()
        rdata2 = type("MockRdata", (), {"preference": 10, "exchange": "mx1.example.com."})()
        mock_answer = [rdata1, rdata2]

        with patch.object(
            dns.asyncresolver.Resolver, "resolve", new_callable=AsyncMock, return_value=mock_answer
        ):
            valid, records = await check_mx("example.com")
            assert valid is True
            assert records == ["mx1.example.com", "mx2.example.com"]

    @pytest.mark.asyncio
    async def test_mx_nxdomain(self) -> None:
        with patch.object(
            dns.asyncresolver.Resolver,
            "resolve",
            new_callable=AsyncMock,
            side_effect=dns.asyncresolver.NXDOMAIN(),
        ):
            valid, records = await check_mx("nonexistent.example.com")
            assert valid is False
            assert records == []

    @pytest.mark.asyncio
    async def test_mx_no_answer(self) -> None:
        with patch.object(
            dns.asyncresolver.Resolver,
            "resolve",
            new_callable=AsyncMock,
            side_effect=dns.asyncresolver.NoAnswer(),
        ):
            valid, records = await check_mx("example.com")
            assert valid is False
            assert records == []

    @pytest.mark.asyncio
    async def test_mx_timeout(self) -> None:
        with patch.object(
            dns.asyncresolver.Resolver,
            "resolve",
            new_callable=AsyncMock,
            side_effect=dns.exception.Timeout(),
        ):
            valid, records = await check_mx("example.com", timeout=0.1)
            assert valid is False
            assert records == []
