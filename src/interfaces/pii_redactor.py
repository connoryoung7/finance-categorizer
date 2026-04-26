from abc import ABC, abstractmethod


class PIIRedactor(ABC):
    """Takes a string that may include PII and removes any PII data that might be found
    in the string."""
    @abstractmethod
    def redact_pii(self, text: str) -> str:
        pass
