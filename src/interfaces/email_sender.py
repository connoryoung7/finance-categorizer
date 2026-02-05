from abc import ABC, abstractmethod

from src.models.budget import Transaction


class EmailSender(ABC):
    """Abstract base class for email sending implementations."""

    @abstractmethod
    def send_transaction_email(self, to_email: str, transaction: Transaction) -> None:
        """
        Send an email.

        Args:
            to_email: Recipient email address.
            subject: Email subject line.
            html_content: HTML content of the email body.
        """
        pass
