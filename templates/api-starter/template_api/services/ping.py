from template_api.exceptions import InvalidInputError
from template_api.schemas.ping import ExamplePingResponse


def build_ping_response(value: str, app_name: str) -> ExamplePingResponse:
    normalized = value.strip()
    if not normalized:
        raise InvalidInputError("value cannot be blank after trimming")

    return ExamplePingResponse(
        original=value,
        normalized=normalized.upper(),
        app_name=app_name,
    )
