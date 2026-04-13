import pytest

from email_validation.services.syntax import check_syntax


class TestSyntaxValidation:
    def test_valid_email(self) -> None:
        valid, reason = check_syntax("user@example.com")
        assert valid is True
        assert reason is None

    def test_valid_email_with_plus(self) -> None:
        valid, _ = check_syntax("user+tag@example.com")
        assert valid is True

    def test_valid_email_with_dots(self) -> None:
        valid, _ = check_syntax("first.last@example.com")
        assert valid is True

    def test_valid_email_with_subdomain(self) -> None:
        valid, _ = check_syntax("user@mail.example.co.uk")
        assert valid is True

    def test_empty_email(self) -> None:
        valid, reason = check_syntax("")
        assert valid is False
        assert reason is not None

    def test_no_at_sign(self) -> None:
        valid, reason = check_syntax("userexample.com")
        assert valid is False
        assert "@ symbol" in reason  # type: ignore[operator]

    def test_no_domain(self) -> None:
        valid, reason = check_syntax("user@")
        assert valid is False
        assert "Empty domain" in reason  # type: ignore[operator]

    def test_no_local_part(self) -> None:
        valid, reason = check_syntax("@example.com")
        assert valid is False
        assert "Empty local" in reason  # type: ignore[operator]

    def test_consecutive_dots(self) -> None:
        valid, reason = check_syntax("user..name@example.com")
        assert valid is False
        assert "Consecutive dots" in reason  # type: ignore[operator]

    def test_leading_dot_local(self) -> None:
        valid, reason = check_syntax(".user@example.com")
        assert valid is False
        assert "start or end with a dot" in reason  # type: ignore[operator]

    def test_trailing_dot_local(self) -> None:
        valid, reason = check_syntax("user.@example.com")
        assert valid is False
        assert "start or end with a dot" in reason  # type: ignore[operator]

    def test_domain_no_tld(self) -> None:
        valid, reason = check_syntax("user@localhost")
        assert valid is False
        assert "at least one dot" in reason  # type: ignore[operator]

    def test_short_tld(self) -> None:
        valid, reason = check_syntax("user@example.x")
        assert valid is False
        assert "Top-level domain" in reason  # type: ignore[operator]

    def test_too_long_email(self) -> None:
        long_local = "a" * 65
        valid, reason = check_syntax(f"{long_local}@example.com")
        assert valid is False

    def test_too_long_total(self) -> None:
        # 254 char limit total
        local = "a" * 64
        domain = "b" * 63 + "." + "c" * 63 + "." + "d" * 63 + ".com"
        email = f"{local}@{domain}"
        if len(email) > 254:
            valid, reason = check_syntax(email)
            assert valid is False

    @pytest.mark.parametrize(
        "email",
        [
            "user@example.com",
            "USER@EXAMPLE.COM",
            "user.name+tag@example.co.uk",
            "x@example.com",
            "test123@test123.com",
        ],
    )
    def test_valid_emails_parametrized(self, email: str) -> None:
        valid, _ = check_syntax(email)
        assert valid is True

    @pytest.mark.parametrize(
        "email",
        [
            "",
            "plainaddress",
            "@no-local.com",
            "user@",
            "user@.com",
            "user@-example.com",
        ],
    )
    def test_invalid_emails_parametrized(self, email: str) -> None:
        valid, _ = check_syntax(email)
        assert valid is False
