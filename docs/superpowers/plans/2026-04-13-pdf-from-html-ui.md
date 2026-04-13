# PDF from HTML — UI Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a self-contained web UI to the pdf-from-html project — login with API key, generate PDFs from a form — fully integrated with the existing auth/rate-limit/metering pipeline via a signed cookie.

**Architecture:** A thin cookie layer translates browser sessions into the existing `x-api-key` auth flow. `CookieToHeaderMiddleware` (pure ASGI) reads a signed HttpOnly cookie and injects the API key header before the shared middleware stack runs. UI routes serve Jinja2 templates; the PDF generation form calls the existing `/v1/generate/pdf` API endpoint via `fetch()` — no duplicate logic. Static assets (HTMX, Pico CSS) are vendored locally for offline/standalone use.

**Tech Stack:** Jinja2 (templates), HTMX (login form), Pico CSS (classless styling), itsdangerous (cookie signing), vanilla JS (PDF download via fetch + blob)

---

## File Structure

**New files:**

| File | Responsibility |
|------|---------------|
| `src/pdf_from_html/middleware/__init__.py` | Package init (empty) |
| `src/pdf_from_html/middleware/cookie_auth.py` | `CookieToHeaderMiddleware` — reads signed cookie, injects `x-api-key` header; redirects unauthenticated UI requests to login |
| `src/pdf_from_html/routes/ui.py` | UI route handlers: login (GET/POST), logout, generate page |
| `src/pdf_from_html/templates/base.html` | Shared layout — nav, CSS/JS includes |
| `src/pdf_from_html/templates/login.html` | Login form — API key input |
| `src/pdf_from_html/templates/generate.html` | PDF generation form — source selector, content input, options, download |
| `src/pdf_from_html/static/js/htmx.min.js` | Vendored HTMX v2 |
| `src/pdf_from_html/static/css/pico.min.css` | Vendored Pico CSS v2 |
| `tests/test_middleware/__init__.py` | Package init (empty) |
| `tests/test_middleware/test_cookie_auth.py` | CookieToHeaderMiddleware unit tests |
| `tests/test_routes/test_ui.py` | UI route tests (login, logout, generate page) |

**Modified files:**

| File | Change |
|------|--------|
| `shared/src/shared/auth/middleware.py` | Add `skip_prefixes` parameter to `AuthMiddleware` |
| `shared/src/shared/rate_limit/middleware.py` | Add `skip_prefixes` parameter to `RateLimitMiddleware` |
| `shared/src/shared/metering/middleware.py` | Add `skip_prefixes` parameter to `MeteringMiddleware` |
| `projects/pdf-from-html/pyproject.toml` | Add `jinja2`, `itsdangerous` dependencies |
| `projects/pdf-from-html/src/pdf_from_html/config.py` | Add `cookie_secret_key` setting |
| `projects/pdf-from-html/src/pdf_from_html/main.py` | Mount static files, add cookie middleware, include UI router, update middleware skip config |
| `projects/pdf-from-html/tests/conftest.py` | Add `COOKIE_SECRET_KEY` env var, add UI test fixtures |

---

### Task 1: Shared Middleware — Add skip_prefixes Support

All three shared middleware classes use exact path matching for their skip lists. UI projects need prefix-based skipping (e.g., `/static/` for assets, `/ui/` for rate-limit/metering bypass). This task adds a backwards-compatible `skip_prefixes` parameter to each.

**Files:**
- Modify: `shared/src/shared/auth/middleware.py:12-19`
- Modify: `shared/src/shared/rate_limit/middleware.py:12-17`
- Modify: `shared/src/shared/metering/middleware.py:12-18`

- [ ] **Step 1: Modify AuthMiddleware to accept skip_prefixes**

In `shared/src/shared/auth/middleware.py`, update the constructor and dispatch method:

```python
class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        skip_paths: frozenset[str] | None = None,
        skip_prefixes: tuple[str, ...] = (),
    ) -> None:
        super().__init__(app)
        self.skip_paths = skip_paths if skip_paths is not None else _SKIP_PATHS
        self.skip_prefixes = skip_prefixes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in self.skip_paths or path.startswith(self.skip_prefixes):
            return await call_next(request)

        channel = getattr(request.state, "channel", "direct")
        # ... rest unchanged
```

- [ ] **Step 2: Modify RateLimitMiddleware to accept skip_prefixes**

In `shared/src/shared/rate_limit/middleware.py`:

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, skip_prefixes: tuple[str, ...] = ()) -> None:
        super().__init__(app)
        self.skip_prefixes = skip_prefixes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in _SKIP_PATHS or path.startswith(self.skip_prefixes):
            return await call_next(request)

        auth: dict[str, object] | None = getattr(request.state, "auth", None)
        # ... rest unchanged
```

- [ ] **Step 3: Modify MeteringMiddleware to accept skip_prefixes**

In `shared/src/shared/metering/middleware.py`:

```python
class MeteringMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, api_name: str, skip_prefixes: tuple[str, ...] = ()) -> None:
        super().__init__(app)
        self.api_name = api_name
        self.skip_prefixes = skip_prefixes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in _SKIP_PATHS or path.startswith(self.skip_prefixes):
            return await call_next(request)

        auth: dict[str, object] | None = getattr(request.state, "auth", None)
        # ... rest unchanged
```

- [ ] **Step 4: Verify existing shared tests still pass**

Run from `shared/`:
```bash
cd /Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/shared && uv run pytest -v
```
Expected: all existing tests PASS (skip_prefixes defaults to empty tuple, no behavior change).

- [ ] **Step 5: Commit**

```bash
git add shared/src/shared/auth/middleware.py shared/src/shared/rate_limit/middleware.py shared/src/shared/metering/middleware.py
git commit -m "feat(shared): add skip_prefixes to auth, rate-limit, and metering middleware

Backwards-compatible — defaults to empty tuple, existing behavior unchanged.
Enables prefix-based path skipping needed by UI-enabled projects."
```

---

### Task 2: Foundation — Dependencies, Config, Static Assets

**Files:**
- Modify: `projects/pdf-from-html/pyproject.toml`
- Modify: `projects/pdf-from-html/src/pdf_from_html/config.py`
- Create: `projects/pdf-from-html/src/pdf_from_html/static/js/htmx.min.js`
- Create: `projects/pdf-from-html/src/pdf_from_html/static/css/pico.min.css`
- Create: `projects/pdf-from-html/src/pdf_from_html/middleware/__init__.py`

- [ ] **Step 1: Add jinja2 and itsdangerous to pyproject.toml**

In `projects/pdf-from-html/pyproject.toml`, update the dependencies list:

```toml
dependencies = [
    "fastapi[standard]>=0.115.0",
    "pydantic-settings>=2.7.0",
    "playwright>=1.52.0",
    "jinja2>=3.1.0",
    "itsdangerous>=2.2.0",
    "shared",
]
```

- [ ] **Step 2: Add cookie_secret_key to Settings**

In `projects/pdf-from-html/src/pdf_from_html/config.py`:

```python
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
    cookie_secret_key: str = "dev-secret-change-in-production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 3: Create middleware package directory**

```bash
touch projects/pdf-from-html/src/pdf_from_html/middleware/__init__.py
```

- [ ] **Step 4: Create static asset directories and vendor HTMX + Pico CSS**

```bash
mkdir -p projects/pdf-from-html/src/pdf_from_html/static/js
mkdir -p projects/pdf-from-html/src/pdf_from_html/static/css
curl -sL -o projects/pdf-from-html/src/pdf_from_html/static/js/htmx.min.js "https://unpkg.com/htmx.org@2/dist/htmx.min.js"
curl -sL -o projects/pdf-from-html/src/pdf_from_html/static/css/pico.min.css "https://unpkg.com/@picocss/pico@2/css/pico.min.css"
```

Verify files were downloaded (should be non-empty):
```bash
wc -c projects/pdf-from-html/src/pdf_from_html/static/js/htmx.min.js
wc -c projects/pdf-from-html/src/pdf_from_html/static/css/pico.min.css
```

- [ ] **Step 5: Install dependencies**

```bash
cd /Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/projects/pdf-from-html && uv sync
```

- [ ] **Step 6: Commit**

```bash
git add projects/pdf-from-html/pyproject.toml projects/pdf-from-html/src/pdf_from_html/config.py projects/pdf-from-html/src/pdf_from_html/middleware/__init__.py projects/pdf-from-html/src/pdf_from_html/static/ projects/pdf-from-html/uv.lock
git commit -m "feat(pdf-from-html): add UI dependencies, config, and vendored static assets

Added jinja2, itsdangerous deps. Vendored HTMX v2 and Pico CSS v2 locally.
Added cookie_secret_key setting for signed session cookies."
```

---

### Task 3: Templates — Base Layout, Login, Generate

**Files:**
- Create: `projects/pdf-from-html/src/pdf_from_html/templates/base.html`
- Create: `projects/pdf-from-html/src/pdf_from_html/templates/login.html`
- Create: `projects/pdf-from-html/src/pdf_from_html/templates/generate.html`

- [ ] **Step 1: Create templates directory**

```bash
mkdir -p projects/pdf-from-html/src/pdf_from_html/templates
```

- [ ] **Step 2: Create base.html**

Create `projects/pdf-from-html/src/pdf_from_html/templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}PDF from HTML{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/pico.min.css">
    <script src="/static/js/htmx.min.js" defer></script>
</head>
<body>
    <header class="container">
        <nav>
            <ul>
                <li><strong>PDF from HTML</strong></li>
            </ul>
            {% if authenticated %}
            <ul>
                <li><a href="/ui/">Generate</a></li>
                <li>
                    <form method="POST" action="/ui/logout" style="margin:0">
                        <button type="submit" class="outline secondary">Logout</button>
                    </form>
                </li>
            </ul>
            {% endif %}
        </nav>
    </header>
    <main class="container">
        {% block content %}{% endblock %}
    </main>
    {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 3: Create login.html**

Create `projects/pdf-from-html/src/pdf_from_html/templates/login.html`:

```html
{% extends "base.html" %}
{% block title %}Login — PDF from HTML{% endblock %}
{% block content %}
<article>
    <header>
        <h2>Enter your API Key</h2>
        <p>Use your API key to access the PDF generator.</p>
    </header>
    {% if error %}
    <p role="alert" style="color: var(--pico-color-red-500);">{{ error }}</p>
    {% endif %}
    <form method="POST" action="/ui/login">
        <label for="api_key">API Key</label>
        <input type="password" id="api_key" name="api_key" required
               placeholder="pk_..." autocomplete="off">
        <button type="submit">Login</button>
    </form>
</article>
{% endblock %}
```

- [ ] **Step 4: Create generate.html**

Create `projects/pdf-from-html/src/pdf_from_html/templates/generate.html`:

```html
{% extends "base.html" %}
{% block title %}Generate PDF — PDF from HTML{% endblock %}
{% block content %}
<article>
    <header>
        <h2>Generate PDF</h2>
    </header>
    <form id="pdf-form">
        <label for="source">Source</label>
        <select id="source" name="source">
            <option value="raw">Raw HTML</option>
            <option value="url">URL</option>
        </select>

        <div id="raw-input">
            <label for="content">HTML Content</label>
            <textarea id="content" name="content" rows="10"
                      placeholder="<html><body><h1>Hello World</h1></body></html>"></textarea>
        </div>
        <div id="url-input" hidden>
            <label for="content-url">URL</label>
            <input type="url" id="content-url" name="content-url"
                   placeholder="https://example.com">
        </div>

        <details>
            <summary>PDF Options</summary>
            <div class="grid">
                <label>
                    Format
                    <select id="opt-format" name="format">
                        <option value="A4" selected>A4</option>
                        <option value="Letter">Letter</option>
                        <option value="Legal">Legal</option>
                        <option value="Tabloid">Tabloid</option>
                    </select>
                </label>
                <label>
                    Orientation
                    <select id="opt-orientation" name="orientation">
                        <option value="portrait" selected>Portrait</option>
                        <option value="landscape">Landscape</option>
                    </select>
                </label>
            </div>
            <div class="grid">
                <label>
                    Scale
                    <input type="number" id="opt-scale" name="scale"
                           value="1.0" min="0.1" max="2.0" step="0.1">
                </label>
                <label>
                    Page Ranges
                    <input type="text" id="opt-page-ranges" name="page_ranges"
                           placeholder="e.g. 1-3, 5">
                </label>
            </div>
            <label>
                <input type="checkbox" id="opt-background" name="print_background" checked>
                Print background
            </label>
        </details>

        <div id="error-message" role="alert"
             style="color: var(--pico-color-red-500); display: none;"></div>
        <div id="success-message" role="status"
             style="color: var(--pico-color-green-500); display: none;"></div>

        <button type="submit" id="submit-btn">Generate PDF</button>
    </form>
</article>
{% endblock %}

{% block scripts %}
<script>
(function () {
    const sourceSelect = document.getElementById("source");
    const rawInput = document.getElementById("raw-input");
    const urlInput = document.getElementById("url-input");
    const form = document.getElementById("pdf-form");
    const submitBtn = document.getElementById("submit-btn");
    const errorDiv = document.getElementById("error-message");
    const successDiv = document.getElementById("success-message");

    sourceSelect.addEventListener("change", function () {
        const isRaw = this.value === "raw";
        rawInput.hidden = !isRaw;
        urlInput.hidden = isRaw;
    });

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        errorDiv.style.display = "none";
        successDiv.style.display = "none";
        submitBtn.disabled = true;
        submitBtn.setAttribute("aria-busy", "true");
        submitBtn.textContent = "Generating\u2026";

        const source = sourceSelect.value;
        const content = source === "raw"
            ? document.getElementById("content").value
            : document.getElementById("content-url").value;

        const options = {
            format: document.getElementById("opt-format").value,
            orientation: document.getElementById("opt-orientation").value,
            scale: parseFloat(document.getElementById("opt-scale").value),
            print_background: document.getElementById("opt-background").checked,
        };
        const pageRanges = document.getElementById("opt-page-ranges").value.trim();
        if (pageRanges) options.page_ranges = pageRanges;

        try {
            const response = await fetch("/v1/generate/pdf", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ source: source, content: content, options: options }),
            });

            if (!response.ok) {
                const data = await response.json();
                errorDiv.textContent = data.detail || "Failed to generate PDF";
                errorDiv.style.display = "block";
                return;
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "document.pdf";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            successDiv.textContent = "PDF downloaded successfully.";
            successDiv.style.display = "block";
        } catch (err) {
            errorDiv.textContent = "Network error \u2014 please try again.";
            errorDiv.style.display = "block";
        } finally {
            submitBtn.disabled = false;
            submitBtn.removeAttribute("aria-busy");
            submitBtn.textContent = "Generate PDF";
        }
    });
})();
</script>
{% endblock %}
```

- [ ] **Step 5: Commit**

```bash
git add projects/pdf-from-html/src/pdf_from_html/templates/
git commit -m "feat(pdf-from-html): add Jinja2 templates for UI

Base layout with Pico CSS + HTMX, login page, PDF generation form.
Generate form calls /v1/generate/pdf via fetch for binary download."
```

---

### Task 4: TDD — CookieToHeaderMiddleware

The middleware reads a signed HttpOnly cookie and injects `x-api-key` into the ASGI scope headers. For UI paths without a valid cookie, it redirects to the login page.

**Files:**
- Create: `projects/pdf-from-html/tests/test_middleware/__init__.py`
- Create: `projects/pdf-from-html/tests/test_middleware/test_cookie_auth.py`
- Create: `projects/pdf-from-html/src/pdf_from_html/middleware/cookie_auth.py`

- [ ] **Step 1: Create test package**

```bash
touch projects/pdf-from-html/tests/test_middleware/__init__.py
```

- [ ] **Step 2: Write failing tests for CookieToHeaderMiddleware**

Create `projects/pdf-from-html/tests/test_middleware/test_cookie_auth.py`:

```python
from http.cookies import SimpleCookie

import pytest
from httpx import ASGITransport, AsyncClient
from itsdangerous import URLSafeSerializer
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from pdf_from_html.middleware.cookie_auth import CookieToHeaderMiddleware

SECRET = "test-secret"
SIGNER = URLSafeSerializer(SECRET, salt="api-key")


def _echo_header_app(request: Request) -> PlainTextResponse:
    """Test app that echoes back the x-api-key header value."""
    value = request.headers.get("x-api-key", "MISSING")
    return PlainTextResponse(value)


def _build_app() -> Starlette:
    app = Starlette(
        routes=[
            Route("/api/test", _echo_header_app),
            Route("/ui/", _echo_header_app),
            Route("/ui/login", _echo_header_app),
        ],
    )
    app.add_middleware(CookieToHeaderMiddleware, secret_key=SECRET)
    return app


@pytest.fixture
def test_app() -> Starlette:
    return _build_app()


@pytest.fixture
async def client(test_app: Starlette) -> AsyncClient:
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestCookieInjection:
    async def test_valid_cookie_injects_header(self, client: AsyncClient) -> None:
        signed = SIGNER.dumps("pk_test_abc123")
        response = await client.get("/api/test", cookies={"api_key": signed})
        assert response.text == "pk_test_abc123"

    async def test_invalid_cookie_does_not_inject_header(self, client: AsyncClient) -> None:
        response = await client.get("/api/test", cookies={"api_key": "tampered-value"})
        assert response.text == "MISSING"

    async def test_no_cookie_no_header(self, client: AsyncClient) -> None:
        response = await client.get("/api/test")
        assert response.text == "MISSING"

    async def test_existing_header_not_overridden(self, client: AsyncClient) -> None:
        signed = SIGNER.dumps("pk_from_cookie")
        response = await client.get(
            "/api/test",
            headers={"x-api-key": "pk_from_header"},
            cookies={"api_key": signed},
        )
        assert response.text == "pk_from_header"


class TestUIRedirect:
    async def test_ui_path_without_cookie_redirects_to_login(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/ui/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/ui/login"

    async def test_login_page_not_redirected(self, client: AsyncClient) -> None:
        response = await client.get("/ui/login")
        assert response.status_code == 200

    async def test_ui_path_with_valid_cookie_passes_through(
        self, client: AsyncClient
    ) -> None:
        signed = SIGNER.dumps("pk_test_key")
        response = await client.get("/ui/", cookies={"api_key": signed})
        assert response.status_code == 200
        assert response.text == "pk_test_key"

    async def test_ui_path_with_invalid_cookie_redirects_to_login(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/ui/", cookies={"api_key": "bad"}, follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/ui/login"

    async def test_non_ui_path_without_cookie_no_redirect(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/api/test")
        assert response.status_code == 200
        assert response.text == "MISSING"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/projects/pdf-from-html && uv run pytest tests/test_middleware/test_cookie_auth.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'pdf_from_html.middleware.cookie_auth'`

- [ ] **Step 4: Implement CookieToHeaderMiddleware**

Create `projects/pdf-from-html/src/pdf_from_html/middleware/cookie_auth.py`:

```python
from itsdangerous import BadSignature, URLSafeSerializer
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send

_LOGIN_PATH = "/ui/login"
_UI_PREFIX = "/ui/"


class CookieToHeaderMiddleware:
    """Read a signed 'api_key' cookie and inject it as an x-api-key header.

    For UI paths (except the login page), redirect to login when no valid
    cookie is present.  API clients that already send the header are
    unaffected — the cookie is never used when the header exists.
    """

    def __init__(self, app: ASGIApp, secret_key: str) -> None:
        self.app = app
        self.signer = URLSafeSerializer(secret_key, salt="api-key")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path = request.url.path
        has_header = "x-api-key" in request.headers

        if has_header:
            await self.app(scope, receive, send)
            return

        cookie_value = request.cookies.get("api_key")
        api_key: str | None = None

        if cookie_value:
            try:
                api_key = self.signer.loads(cookie_value)
            except BadSignature:
                api_key = None

        if api_key:
            scope["headers"] = [*scope["headers"], (b"x-api-key", api_key.encode())]
            await self.app(scope, receive, send)
            return

        # No valid credential — redirect to login for UI paths
        if path.startswith(_UI_PREFIX) and path != _LOGIN_PATH:
            response = RedirectResponse(_LOGIN_PATH)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd /Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/projects/pdf-from-html && uv run pytest tests/test_middleware/test_cookie_auth.py -v
```
Expected: all 9 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add projects/pdf-from-html/src/pdf_from_html/middleware/cookie_auth.py projects/pdf-from-html/tests/test_middleware/
git commit -m "feat(pdf-from-html): add CookieToHeaderMiddleware with tests

Reads signed HttpOnly cookie, injects x-api-key header into ASGI scope.
Redirects unauthenticated UI requests to login page.
API clients with existing header are unaffected."
```

---

### Task 5: TDD — UI Routes (Login, Logout, Generate Page)

**Files:**
- Create: `projects/pdf-from-html/tests/test_routes/test_ui.py`
- Create: `projects/pdf-from-html/src/pdf_from_html/routes/ui.py`

- [ ] **Step 1: Write failing tests for UI routes**

Create `projects/pdf-from-html/tests/test_routes/test_ui.py`:

```python
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from itsdangerous import URLSafeSerializer

from pdf_from_html.middleware.cookie_auth import CookieToHeaderMiddleware

COOKIE_SECRET = "test-cookie-secret"
SIGNER = URLSafeSerializer(COOKIE_SECRET, salt="api-key")


@pytest.fixture
async def ui_client(app) -> AsyncClient:  # type: ignore[no-untyped-def]
    """HTTP client without API key header — uses cookies like a browser."""
    # Wrap the app with CookieToHeaderMiddleware for realistic testing
    wrapped = CookieToHeaderMiddleware(app, secret_key=COOKIE_SECRET)
    transport = ASGITransport(app=wrapped)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestLoginPage:
    async def test_get_login_renders_form(self, ui_client: AsyncClient) -> None:
        response = await ui_client.get("/ui/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "API Key" in response.text

    async def test_post_login_valid_key_sets_cookie_and_redirects(
        self, ui_client: AsyncClient, app: MagicMock
    ) -> None:
        api_key = app.state._test_api_key  # noqa: SLF001
        response = await ui_client.post(
            "/ui/login",
            data={"api_key": api_key},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/"
        assert "api_key" in response.cookies

    async def test_post_login_invalid_key_shows_error(
        self, ui_client: AsyncClient
    ) -> None:
        response = await ui_client.post(
            "/ui/login",
            data={"api_key": "pk_invalid_key_12345678"},
        )
        assert response.status_code == 200
        assert "Invalid" in response.text or "invalid" in response.text


class TestLogout:
    async def test_logout_clears_cookie_and_redirects(
        self, ui_client: AsyncClient, app: MagicMock
    ) -> None:
        # First login to get a cookie
        api_key = app.state._test_api_key  # noqa: SLF001
        login_resp = await ui_client.post(
            "/ui/login",
            data={"api_key": api_key},
            follow_redirects=False,
        )
        cookies = login_resp.cookies

        response = await ui_client.post(
            "/ui/logout",
            cookies=dict(cookies),
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/login"
        # Cookie should be cleared (max_age=0)
        assert "api_key" in response.headers.get("set-cookie", "")


class TestGeneratePage:
    async def test_authenticated_user_sees_generate_form(
        self, ui_client: AsyncClient, app: MagicMock
    ) -> None:
        api_key = app.state._test_api_key  # noqa: SLF001
        signed = SIGNER.dumps(api_key)
        response = await ui_client.get("/ui/", cookies={"api_key": signed})
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Generate PDF" in response.text

    async def test_unauthenticated_user_redirected_to_login(
        self, ui_client: AsyncClient
    ) -> None:
        response = await ui_client.get("/ui/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/ui/login"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/projects/pdf-from-html && uv run pytest tests/test_routes/test_ui.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'pdf_from_html.routes.ui'`

- [ ] **Step 3: Implement UI routes**

Create `projects/pdf-from-html/src/pdf_from_html/routes/ui.py`:

```python
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer
from shared.auth.api_key import validate_api_key_direct

from pdf_from_html.config import Settings, get_settings

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

router = APIRouter(prefix="/ui", tags=["ui"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


def _get_signer(settings: Settings) -> URLSafeSerializer:
    return URLSafeSerializer(settings.cookie_secret_key, salt="api-key")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html", {"authenticated": False})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    settings: SettingsDep,
    api_key: Annotated[str, Form()],
) -> HTMLResponse | RedirectResponse:
    redis = request.app.state.redis
    session_factory = request.app.state.db_session_factory

    try:
        async with session_factory() as session:
            await validate_api_key_direct(api_key, redis, session)
    except Exception:
        return templates.TemplateResponse(
            request, "login.html", {"authenticated": False, "error": "Invalid API key."}
        )

    signer = _get_signer(settings)
    signed_key = signer.dumps(api_key)
    response = RedirectResponse("/ui/", status_code=303)
    response.set_cookie(
        "api_key",
        signed_key,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return response


@router.post("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse("/ui/login", status_code=303)
    response.delete_cookie("api_key")
    return response


@router.get("/", response_class=HTMLResponse)
async def generate_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "generate.html", {"authenticated": True})
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/projects/pdf-from-html && uv run pytest tests/test_routes/test_ui.py -v
```
Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add projects/pdf-from-html/src/pdf_from_html/routes/ui.py projects/pdf-from-html/tests/test_routes/test_ui.py
git commit -m "feat(pdf-from-html): add UI routes with tests

Login (GET/POST), logout, and generate page routes.
Login validates API key via shared auth, sets signed cookie.
Generate page requires authentication via cookie."
```

---

### Task 6: Wire Up main.py — Middleware, Static Mount, Router

**Files:**
- Modify: `projects/pdf-from-html/src/pdf_from_html/main.py`

- [ ] **Step 1: Update main.py with all UI integrations**

Replace the full contents of `projects/pdf-from-html/src/pdf_from_html/main.py`:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from playwright.async_api import async_playwright
from shared import (
    AuthMiddleware,
    ChannelDetectMiddleware,
    MeteringMiddleware,
    RateLimitMiddleware,
    setup_shared,
)

from pdf_from_html.config import get_settings
from pdf_from_html.exceptions import AppError, app_exception_handler
from pdf_from_html.middleware.cookie_auth import CookieToHeaderMiddleware
from pdf_from_html.routes.generate import router as generate_router
from pdf_from_html.routes.ui import router as ui_router
from pdf_from_html.services.browser_pool import BrowserPool

_STATIC_DIR = Path(__file__).resolve().parent / "static"

# Auth skip paths: default shared paths + public UI paths
_AUTH_SKIP_PATHS = frozenset({
    "/health", "/docs", "/redoc", "/openapi.json", "/webhooks/stripe",
    "/ui/login",
})

# Rate-limit and metering skip prefixes: UI pages and static assets
# should not consume API quota — only /v1/* endpoints are metered.
_QUOTA_SKIP_PREFIXES = ("/ui/", "/static/")

# Auth skip prefixes: static assets don't require authentication
_AUTH_SKIP_PREFIXES = ("/static/",)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with setup_shared(app, settings):
        pw = await async_playwright().start()
        browser = await pw.chromium.launch()
        app.state.browser_pool = BrowserPool(browser, settings.browser_pool_size)
        try:
            yield
        finally:
            await app.state.browser_pool.close()
            await pw.stop()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PDF from HTML API",
        description=(
            "Generate PDFs from raw HTML or URLs using Chromium. "
            "Pixel-perfect rendering with full CSS3 and JavaScript support."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_exception_handler(AppError, app_exception_handler)  # type: ignore[arg-type]

    # Middleware stack (last added = outermost = runs first on request)
    # 5. MeteringMiddleware — innermost, tracks API usage
    app.add_middleware(
        MeteringMiddleware,
        api_name="pdf-from-html",
        skip_prefixes=_QUOTA_SKIP_PREFIXES,
    )
    # 4. RateLimitMiddleware — enforces per-minute rate limits
    app.add_middleware(RateLimitMiddleware, skip_prefixes=_QUOTA_SKIP_PREFIXES)
    # 3. AuthMiddleware — validates API key (from header or injected by cookie middleware)
    app.add_middleware(
        AuthMiddleware,
        skip_paths=_AUTH_SKIP_PATHS,
        skip_prefixes=_AUTH_SKIP_PREFIXES,
    )
    # 2. ChannelDetectMiddleware — sets request.state.channel
    app.add_middleware(ChannelDetectMiddleware)
    # 1. CookieToHeaderMiddleware — outermost, reads cookie and injects x-api-key header
    app.add_middleware(CookieToHeaderMiddleware, secret_key=settings.cookie_secret_key)

    # Static files
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    # Routers
    app.include_router(generate_router)
    app.include_router(ui_router)

    # DEVIATION: bare dict return instead of Pydantic model — health check
    # endpoint intentionally returns minimal unstructured response
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 2: Run all existing tests to verify nothing is broken**

```bash
cd /Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/projects/pdf-from-html && uv run pytest -v
```
Expected: all existing tests PASS, plus UI and middleware tests PASS.

- [ ] **Step 3: Commit**

```bash
git add projects/pdf-from-html/src/pdf_from_html/main.py
git commit -m "feat(pdf-from-html): wire up UI — middleware, static files, router

CookieToHeaderMiddleware runs outermost, injecting API key from cookie.
AuthMiddleware skips /static/ prefix and /ui/login path.
RateLimit and Metering skip /ui/ and /static/ prefixes.
Static files served from /static/, UI routes from /ui/."
```

---

### Task 7: Update Test Fixtures and Add conftest Changes

**Files:**
- Modify: `projects/pdf-from-html/tests/conftest.py`

- [ ] **Step 1: Add COOKIE_SECRET_KEY env var to test fixtures**

In `projects/pdf-from-html/tests/conftest.py`, add the env var to the `_test_env` fixture:

```python
@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set env vars required by SharedSettings."""
    monkeypatch.setenv("APP_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("APP_REDIS_URL", "redis://localhost")
    monkeypatch.setenv("COOKIE_SECRET_KEY", "test-cookie-secret")
```

- [ ] **Step 2: Run the full test suite**

```bash
cd /Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/projects/pdf-from-html && uv run pytest -v
```
Expected: ALL tests PASS.

- [ ] **Step 3: Run with coverage to verify adequate coverage**

```bash
cd /Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/projects/pdf-from-html && uv run pytest --cov=src/pdf_from_html --cov-report=term-missing
```
Expected: new files (middleware/cookie_auth.py, routes/ui.py) should have coverage.

- [ ] **Step 4: Run linting and type checking**

```bash
cd /Users/c-sikawats/Documents/GitHub/Personal/fastapi-cloud-apis/projects/pdf-from-html && uv run ruff check . && uv run ruff format --check . && uv run mypy src/
```
Expected: no lint errors, no type errors.

- [ ] **Step 5: Commit**

```bash
git add projects/pdf-from-html/tests/conftest.py
git commit -m "chore(pdf-from-html): add COOKIE_SECRET_KEY to test env fixtures"
```

---

## Auth Flow Summary

After all tasks are complete, the request flow is:

```
Browser Request
       │
       ▼
CookieToHeaderMiddleware (outermost)
  ├─ Has x-api-key header? → pass through (API client)
  ├─ Has valid signed cookie? → inject x-api-key header, pass through
  ├─ UI path without cookie? → redirect to /ui/login
  └─ Non-UI path without cookie? → pass through
       │
       ▼
ChannelDetectMiddleware → sets channel (direct/rapidapi)
       │
       ▼
AuthMiddleware
  ├─ /ui/login or /static/* → skip auth
  └─ All other paths → validate x-api-key (from header or cookie injection)
       │
       ▼
RateLimitMiddleware
  ├─ /ui/* or /static/* → skip rate limiting
  └─ /v1/* → enforce per-minute rate limit
       │
       ▼
MeteringMiddleware
  ├─ /ui/* or /static/* → skip metering
  └─ /v1/* → track API usage, enforce monthly quota
       │
       ▼
Route Handler
```

**Key design property:** UI users hit the same `/v1/generate/pdf` endpoint via `fetch()`. That call goes through full auth + rate limiting + metering. Only page views and static assets skip quota tracking.
