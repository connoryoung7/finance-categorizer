from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from src.interfaces.pii_redactor import PIIRedactor

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
    "NRP": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_NRP>"},
    ),
    "LOCATION": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_LOCATION>"},
    ),
    "PERSON": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_PERSON>"},
    ),
    "PHONE_NUMBER": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_PHONE_NUMBER>"},
    ),
    "MEDICAL_LICENSE": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_MEDICAL_LICENSE>"},
    ),
    "URL": OperatorConfig(
        operator_name="replace",
        params={"new_value": "<REDACTED_URL>"},
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


class PresidioPIIRedactor(PIIRedactor):
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def redact_pii(self, text: str) -> str:
        analysis_results = self.analyzer.analyze(text=text, language="en")
        return self.anonymizer.anonymize(
            text=text, analyzer_results=analysis_results, operators=operators
        ).text
