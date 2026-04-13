import fakeredis.aioredis

from qr_code_generator.schemas.generate import QRCodeRequest


class TestCaching:
    async def test_cache_miss_stores_result(self) -> None:
        from qr_code_generator.services.generator import generate_qr_cached

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        params = QRCodeRequest(data="cache-test")

        result = await generate_qr_cached(params, None, redis, cache_ttl=3600)

        assert result[:8] == b"\x89PNG\r\n\x1a\n"
        keys = await redis.keys("qr:*")
        assert len(keys) == 1
        await redis.aclose()

    async def test_cache_hit_returns_cached(self) -> None:
        from qr_code_generator.services.generator import generate_qr_cached

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        params = QRCodeRequest(data="cache-test-2")

        first = await generate_qr_cached(params, None, redis, cache_ttl=3600)
        second = await generate_qr_cached(params, None, redis, cache_ttl=3600)

        assert first == second
        await redis.aclose()

    async def test_different_params_different_cache_keys(self) -> None:
        from qr_code_generator.services.generator import generate_qr_cached

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

        params_a = QRCodeRequest(data="aaa")
        params_b = QRCodeRequest(data="bbb")

        await generate_qr_cached(params_a, None, redis, cache_ttl=3600)
        await generate_qr_cached(params_b, None, redis, cache_ttl=3600)

        keys = await redis.keys("qr:*")
        assert len(keys) == 2
        await redis.aclose()

    async def test_logo_included_in_cache_key(self) -> None:
        import io

        from PIL import Image

        from qr_code_generator.services.generator import generate_qr_cached

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        params = QRCodeRequest(data="logo-cache-test")

        logo_a = io.BytesIO()
        Image.new("RGBA", (10, 10), (255, 0, 0, 255)).save(logo_a, format="PNG")

        logo_b = io.BytesIO()
        Image.new("RGBA", (10, 10), (0, 255, 0, 255)).save(logo_b, format="PNG")

        await generate_qr_cached(params, logo_a.getvalue(), redis, cache_ttl=3600)
        await generate_qr_cached(params, logo_b.getvalue(), redis, cache_ttl=3600)

        keys = await redis.keys("qr:*")
        assert len(keys) == 2
        await redis.aclose()

    async def test_cache_ttl_set(self) -> None:
        from qr_code_generator.services.generator import generate_qr_cached

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        params = QRCodeRequest(data="ttl-test")

        await generate_qr_cached(params, None, redis, cache_ttl=120)

        keys = await redis.keys("qr:*")
        ttl = await redis.ttl(keys[0])
        assert 0 < ttl <= 120
        await redis.aclose()
