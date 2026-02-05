import pytest

from src.services.pii_redactor import PIIRedactor


@pytest.fixture
def redactor():
    return PIIRedactor()


class TestPIIRedactor:
    def test_redact_credit_card(self, redactor):
        text = "My credit card number is 4532015112830366."
        result = redactor.redact_pii(text)
        assert "<REDACTED_CREDIT_CARD>" in result
        assert "4532015112830366" not in result

    def test_redact_email_address(self, redactor):
        text = "Contact me at john.doe@example.com for more info."
        result = redactor.redact_pii(text)
        assert "<REDACTED_EMAIL_ADDRESS>" in result
        assert "john.doe@example.com" not in result

    def test_redact_phone_number(self, redactor):
        text = "Call me at 555-123-4567."
        result = redactor.redact_pii(text)
        assert "<REDACTED_PHONE_NUMBER>" in result
        assert "555-123-4567" not in result

    def test_redact_us_ssn(self, redactor):
        text = "My social security number is 078-05-1120."
        result = redactor.redact_pii(text)
        # SSN may be detected as SSN or phone number depending on context
        assert "078-05-1120" not in result
        assert "<REDACTED_" in result

    def test_redact_ip_address(self, redactor):
        text = "The server IP is 192.168.1.100."
        result = redactor.redact_pii(text)
        assert "<REDACTED_IP_ADDRESS>" in result
        assert "192.168.1.100" not in result

    def test_redact_iban(self, redactor):
        text = "Transfer to IBAN DE89370400440532013000."
        result = redactor.redact_pii(text)
        assert "<REDACTED_IBAN_CODE>" in result
        assert "DE89370400440532013000" not in result

    def test_redact_url(self, redactor):
        text = "Visit https://www.example.com/secret for details."
        result = redactor.redact_pii(text)
        assert "<REDACTED_URL>" in result
        assert "https://www.example.com/secret" not in result

    def test_redact_person_name(self, redactor):
        text = "The package was sent to John Smith at the address."
        result = redactor.redact_pii(text)
        assert "<REDACTED_PERSON>" in result
        assert "John Smith" not in result

    def test_redact_multiple_pii(self, redactor):
        text = "John Doe (john.doe@example.com) called from 555-123-4567."
        result = redactor.redact_pii(text)
        assert "<REDACTED_EMAIL_ADDRESS>" in result
        assert "<REDACTED_PHONE_NUMBER>" in result
        assert "john.doe@example.com" not in result
        assert "555-123-4567" not in result

    def test_no_pii_unchanged(self, redactor):
        text = "This is a normal sentence with no sensitive data."
        result = redactor.redact_pii(text)
        assert result == text

    def test_empty_string(self, redactor):
        text = ""
        result = redactor.redact_pii(text)
        assert result == ""
