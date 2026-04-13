from email_validation.services.role_based import is_role_based


class TestRoleBased:
    def test_admin(self) -> None:
        assert is_role_based("admin@example.com") is True

    def test_info(self) -> None:
        assert is_role_based("info@example.com") is True

    def test_support(self) -> None:
        assert is_role_based("support@example.com") is True

    def test_noreply(self) -> None:
        assert is_role_based("noreply@example.com") is True

    def test_no_reply_hyphen(self) -> None:
        assert is_role_based("no-reply@example.com") is True

    def test_postmaster(self) -> None:
        assert is_role_based("postmaster@example.com") is True

    def test_webmaster(self) -> None:
        assert is_role_based("webmaster@example.com") is True

    def test_personal_email(self) -> None:
        assert is_role_based("john@example.com") is False

    def test_personal_with_numbers(self) -> None:
        assert is_role_based("john123@example.com") is False

    def test_case_insensitive(self) -> None:
        assert is_role_based("ADMIN@example.com") is True
        assert is_role_based("Info@example.com") is True
