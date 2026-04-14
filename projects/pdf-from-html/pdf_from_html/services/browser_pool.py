import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from playwright.async_api import Browser, Page

from pdf_from_html.exceptions import BrowserPoolExhaustedError

_ACQUIRE_TIMEOUT = 5.0


class BrowserPool:
    """Manages a pool of Playwright browser contexts with bounded concurrency."""

    def __init__(self, browser: Browser, pool_size: int) -> None:
        self._browser = browser
        self._semaphore = asyncio.Semaphore(pool_size)

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Page]:
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=_ACQUIRE_TIMEOUT)
        except TimeoutError as exc:
            raise BrowserPoolExhaustedError() from exc

        try:
            context = await self._browser.new_context()
            page = await context.new_page()
        except Exception:
            self._semaphore.release()
            raise

        try:
            yield page
        finally:
            await page.close()
            await context.close()
            self._semaphore.release()

    async def close(self) -> None:
        await self._browser.close()
