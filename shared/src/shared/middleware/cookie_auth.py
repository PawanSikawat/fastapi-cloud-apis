from itsdangerous import BadSignature, URLSafeSerializer
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send

_LOGIN_PATH = "/ui/login"
_LOGOUT_PATH = "/ui/logout"
_UI_PREFIX = "/ui/"


class CookieToHeaderMiddleware:
    """Read a signed 'api_key' cookie and inject it as an x-api-key header.

    For UI paths (except the login page), redirect to login when no valid
    cookie is present. API clients that already send the header are
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

        if path.startswith(_UI_PREFIX) and path not in {_LOGIN_PATH, _LOGOUT_PATH}:
            response = RedirectResponse(_LOGIN_PATH)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
