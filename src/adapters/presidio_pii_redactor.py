from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from src.interfaces.pii_redactor import PIIRedactor

# Only unambiguous identifiers are redacted.
#
# PERSON, LOCATION, NRP and URL are deliberately absent. Receipts are mostly
# product names, and Presidio's NER reads many of them as people or places --
# "Ham Jamboree", "American Classic", "French Toast Four Pack". Redacting those
# destroys the line items this pipeline exists to extract, and URL redaction
# strips vendor item identifiers (e.g. an Amazon ASIN) along with them.
operators = {
    "CREDIT_CARD": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_CREDIT_CARD>"},
    ),
    "CRYPTO": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_CRYPTO>"},
    ),
    "EMAIL_ADDRESS": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_EMAIL_ADDRESS>"},
    ),
    "IBAN_CODE": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_IBAN_CODE>"},
    ),
    "IP_ADDRESS": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_IP_ADDRESS>"},
    ),
    "PHONE_NUMBER": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_PHONE_NUMBER>"},
    ),
    "US_BANK_NUMBER": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_US_BANK_NUMBER>"},
    ),
    "US_DRIVER_LICENSE": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_US_DRIVER_LICENSE>"},
    ),
    "US_ITIN": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_US_ITIN>"},
    ),
    "US_PASSPORT": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_US_PASSPORT>"},
    ),
    "US_SSN": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_US_SSN>"},
    ),
}

REDACTED_ENTITIES = list(operators)


class PresidioPIIRedactor(PIIRedactor):
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def redact_pii(self, text: str) -> str:
        analysis_results = self.analyzer.analyze(
            text=text, language="en", entities=REDACTED_ENTITIES
        )
        return self.anonymizer.anonymize(
            text=text, analyzer_results=analysis_results, operators=operators
        ).text
