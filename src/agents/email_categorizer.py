from typing_extensions import final

from pydantic_ai import Agent

from src.models.email import Email, EmailCategory
from src.services.pii_redactor import PIIRedactor


class EmailCategorizerAgent:
    """
    Docstring for EmailCategorizerAgent
    """
    def __init__(self, llm_client: Agent, pii_redactor: PIIRedactor):
        self.llm_client = llm_client
        self.pii_redactor = pii_redactor

    def categorize_email_content(self, email: Email) -> EmailCategory:
        """
        
        
        :param self: Description
        :param email: The incoming email that was sent to the personan inbox
        :type email: Email
        :return: Description
        :rtype: EmailCategory
        """
        if email.from_ == "auto-confirm@amazon.com":
            # Process Amazon purchase confirmation emails
            pass

        redacted_email_content = self.pii_redactor.redact_pii(email.content)
        pass

    @final
    @property
    def company_emails() -> dict[str, str]:
        """
        A mapping of company names to their associated email domains.

        :return: A dictionary where keys are email domains and values are company names.
        :rtype: dict[str, str]
        """
        return {
            "amazon.com": "Amazon",
            "ebay.com": "eBay",
            "walmart.com": "Walmart",
            "target.com": "Target",
            "bestbuy.com": "Best Buy",
        }

    def _find_company_from_email(self, from_email: str) -> str | None:
        """
        Extract the company name from the email content.

        :param email: The email object containing the content.
        :type email: Email
        :return: The extracted company name or None if not found.
        :rtype: str | None
        """
        email_domain = from_email.split("@")[-1]
        if not email_domain in self.company_emails:
            return None
        return self.company_emails[email_domain]
        