import pytest

from src.adapters.presidio_pii_redactor import PresidioPIIRedactor


@pytest.fixture
def redactor():
    return PresidioPIIRedactor()


class TestPresidioPIIRedactor:
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

    def test_urls_are_preserved(self, redactor):
        # URLs carry vendor item identifiers (e.g. an Amazon ASIN), which are
        # sometimes the only remaining trace of what was purchased.
        text = "Visit https://www.amazon.com/dp/B08QPTNTQ5 for details."
        result = redactor.redact_pii(text)
        assert "https://www.amazon.com/dp/B08QPTNTQ5" in result

    def test_person_names_are_preserved(self, redactor):
        # PERSON is off because Presidio's NER cannot tell a customer name from
        # a product name, and losing product names defeats the pipeline.
        text = "The package was sent to John Smith at the address."
        result = redactor.redact_pii(text)
        assert "John Smith" in result

    def test_product_names_survive_redaction(self, redactor):
        # Real line items from parsed_messages/no-reply@toasttab.com -- these
        # are exactly the strings a PERSON/LOCATION/NRP recognizer would eat.
        text = (
            "Classic Four Pack $10.00\n"
            "French Toast Four Pack $10.00\n"
            "Anadama Four Pack $10.00\n"
            "Ham Jamboree $11.00\n"
            "American Classic $7.00\n"
            "Lg (24 oz) Matcha Lemonade $5.50\n"
        )
        result = redactor.redact_pii(text)
        for item in [
            "Classic Four Pack",
            "French Toast Four Pack",
            "Anadama Four Pack",
            "Ham Jamboree",
            "American Classic",
            "Matcha Lemonade",
        ]:
            assert item in result
        assert "<REDACTED_" not in result

    def test_hard_identifiers_still_redacted_alongside_product_names(self, redactor):
        text = (
            "Ham Jamboree $11.00\n"
            "Paid with card 4532015112830366\n"
            "SSN 078-05-1120\n"
        )
        result = redactor.redact_pii(text)
        assert "Ham Jamboree" in result
        assert "4532015112830366" not in result
        assert "078-05-1120" not in result

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
