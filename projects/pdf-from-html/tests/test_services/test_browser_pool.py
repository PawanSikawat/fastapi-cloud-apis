from unittest.mock import AsyncMock, MagicMock

import pytest


def _mock_browser() -> MagicMock:
    """Create a mock Playwright Browser that produces mock contexts and pages."""
    browser = MagicMock()
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    browser.new_context = AsyncMock(return_value=mock_context)
    browser.close = AsyncMock()
    return browser


class TestBrowserPool:
    async def test_acquire_yields_page(self) -> None:
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=2)
        async with pool.acquire() as page:
            assert page is not None
        browser.new_context.assert_awaited_once()

    async def test_page_and_context_closed_after_release(self) -> None:
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=2)
        async with pool.acquire() as page:
            context = browser.new_context.return_value
        page.close.assert_awaited_once()
        context.close.assert_awaited_once()

    async def test_pool_exhaustion_raises_error(self) -> None:
        from pdf_from_html.exceptions import BrowserPoolExhaustedError
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=1)

        async with pool.acquire():
            with pytest.raises(BrowserPoolExhaustedError):
                async with pool.acquire():
                    pass

    async def test_semaphore_released_after_use(self) -> None:
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=1)

        async with pool.acquire():
            pass

        # Should succeed — semaphore was released
        async with pool.acquire():
            pass

    async def test_semaphore_released_on_exception(self) -> None:
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=1)

        with pytest.raises(RuntimeError):
            async with pool.acquire():
                raise RuntimeError("boom")

        # Should succeed — semaphore was released despite exception
        async with pool.acquire():
            pass

    async def test_close_closes_browser(self) -> None:
        from pdf_from_html.services.browser_pool import BrowserPool

        browser = _mock_browser()
        pool = BrowserPool(browser, pool_size=2)
        await pool.close()
        browser.close.assert_awaited_once()
