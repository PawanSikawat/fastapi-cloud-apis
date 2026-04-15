from pydantic import BaseModel, Field


class ExamplePingRequest(BaseModel):
    value: str = Field(min_length=1, max_length=200)


class ExamplePingResponse(BaseModel):
    original: str
    normalized: str
    app_name: str
