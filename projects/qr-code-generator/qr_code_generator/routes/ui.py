from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer
from shared.auth.api_key import validate_api_key_direct

from qr_code_generator.config import Settings, get_settings

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

router = APIRouter(prefix="/ui", tags=["ui"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


def _get_signer(settings: Settings) -> URLSafeSerializer:
    return URLSafeSerializer(settings.cookie_secret_key, salt="api-key")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html", {"authenticated": False})


@router.post("/login", response_model=None)
async def login_submit(
    request: Request,
    settings: SettingsDep,
    api_key: Annotated[str, Form()],
) -> Response:
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
