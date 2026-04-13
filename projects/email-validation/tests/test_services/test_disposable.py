from email_validation.services.disposable import is_disposable


class TestDisposable:
    def test_known_disposable(self) -> None:
        assert is_disposable("mailinator.com") is True

    def test_known_disposable_guerrillamail(self) -> None:
        assert is_disposable("guerrillamail.com") is True

    def test_known_disposable_tempmail(self) -> None:
        assert is_disposable("temp-mail.org") is True

    def test_known_disposable_yopmail(self) -> None:
        assert is_disposable("yopmail.com") is True

    def test_not_disposable_gmail(self) -> None:
        assert is_disposable("gmail.com") is False

    def test_not_disposable_company(self) -> None:
        assert is_disposable("company.com") is False

    def test_case_insensitive(self) -> None:
        assert is_disposable("MAILINATOR.COM") is True
        assert is_disposable("Mailinator.Com") is True
