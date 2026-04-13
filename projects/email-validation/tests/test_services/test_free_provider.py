from email_validation.services.free_provider import is_free_provider


class TestFreeProvider:
    def test_gmail(self) -> None:
        assert is_free_provider("gmail.com") is True

    def test_yahoo(self) -> None:
        assert is_free_provider("yahoo.com") is True

    def test_outlook(self) -> None:
        assert is_free_provider("outlook.com") is True

    def test_hotmail(self) -> None:
        assert is_free_provider("hotmail.com") is True

    def test_protonmail(self) -> None:
        assert is_free_provider("protonmail.com") is True

    def test_icloud(self) -> None:
        assert is_free_provider("icloud.com") is True

    def test_company_domain(self) -> None:
        assert is_free_provider("company.com") is False

    def test_custom_domain(self) -> None:
        assert is_free_provider("mydomain.io") is False

    def test_case_insensitive(self) -> None:
        assert is_free_provider("GMAIL.COM") is True
        assert is_free_provider("Gmail.Com") is True
