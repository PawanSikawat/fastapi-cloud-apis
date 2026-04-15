from httpx import AsyncClient


async def test_ping_example(client: AsyncClient) -> None:
    response = await client.post("/v1/example/ping", json={"value": "hello"})
    assert response.status_code == 200
    assert response.json() == {
        "original": "hello",
        "normalized": "HELLO",
        "app_name": "Starter API",
    }
