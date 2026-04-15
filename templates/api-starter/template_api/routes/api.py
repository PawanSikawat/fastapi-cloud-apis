from typing import Annotated

from fastapi import APIRouter, Depends

from template_api.config import Settings, get_settings
from template_api.schemas.ping import ExamplePingRequest, ExamplePingResponse
from template_api.services.ping import build_ping_response

router = APIRouter(prefix="/v1/example", tags=["example"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("/ping", response_model=ExamplePingResponse)
async def ping_example(
    body: ExamplePingRequest,
    settings: SettingsDep,
) -> ExamplePingResponse:
    """Example endpoint to replace with the real product API."""
    return build_ping_response(body.value, app_name=settings.app_name)
