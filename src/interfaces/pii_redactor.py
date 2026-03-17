from abc import ABC, abstractmethod


class PIIRedactor(ABC):
    @abstractmethod
    def redact_pii(self, text: str) -> str:
        pass
