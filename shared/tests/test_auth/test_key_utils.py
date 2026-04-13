from shared.auth.key_utils import generate_api_key, hash_api_key


class TestKeyUtils:
    def test_generate_api_key_format(self) -> None:
        full_key, prefix, key_hash = generate_api_key()
        assert full_key.startswith("sk_")
        assert prefix == full_key[:12]
        assert len(key_hash) == 64

    def test_generate_api_key_custom_prefix(self) -> None:
        full_key, _, _ = generate_api_key(prefix="ev")
        assert full_key.startswith("ev_")

    def test_generate_api_key_unique(self) -> None:
        key1, _, _ = generate_api_key()
        key2, _, _ = generate_api_key()
        assert key1 != key2

    def test_hash_api_key_deterministic(self) -> None:
        h1 = hash_api_key("test-key")
        h2 = hash_api_key("test-key")
        assert h1 == h2

    def test_hash_api_key_different_inputs(self) -> None:
        h1 = hash_api_key("key-a")
        h2 = hash_api_key("key-b")
        assert h1 != h2

    def test_generate_and_hash_roundtrip(self) -> None:
        full_key, _, expected_hash = generate_api_key()
        assert hash_api_key(full_key) == expected_hash
