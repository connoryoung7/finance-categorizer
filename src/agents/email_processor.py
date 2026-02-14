import re
from typing import final

from html_to_markdown import convert_to_markdown
from pydantic_ai import Agent

from src.models.email import Email, EmailCategory
from src.models.order import Order
from src.services.pii_redactor import PIIRedactor


class EmailProcessorAgent:
    """Agent for processing and categorizing emails.

    Handles email categorization (receipt, invoice, newsletter, etc.)
    and extracts order details from receipt emails.
    """
    def __init__(self, llm_client: Agent, pii_redactor: PIIRedactor):
        self.llm_client = llm_client
        self.pii_redactor = pii_redactor

    def categorize_email(self, email: Email) -> EmailCategory:
        """Categorize an email based on its subject line.

        First attempts to categorize by subject. Falls back to content
        analysis if subject is inconclusive.

        :param email: The email to categorize.
        :return: The determined email category.
        """
        email_category = self._categorize_email_subject(email.subject)
        if email_category == EmailCategory.RECEIPT:
            return EmailCategory.RECEIPT
        else:
            pass
            # return self._categorize_email_content(email)

    def process_email_content(self, email: Email) -> Order | None:
        """
        Process the content of a receipt email and extract order details.
        """
        # category = self._categorize_email_content(email)

        # if category == EmailCategory.RECEIPT:
        #     # TODO: Implement receipt processing logic
        #     pass
        pass
            

    def _categorize_email_content(self, email: Email) -> EmailCategory:
        """Categorize an email based on its body content using LLM analysis.

        Converts the email to markdown, redacts PII, and uses the LLM
        to determine the category.

        :param email: The email to categorize.
        :return: The determined email category.
        """
        redacted_markdown = self._convert_email_to_markdown(email)

        prompt = f"""
        Categorize the following email content into one of these categories:
- receipt: Purchase receipts or payment confirmations
- order_confirmation: Order placement confirmations
- shipping_notification: Shipping or delivery updates
- newsletter: Newsletter subscriptions
- promotional: Marketing or promotional emails
- transaction_alert: Bank or financial transaction alerts
- other: Any other type of email

Email content:
{redacted_markdown}

Respond with only the category name (e.g., "receipt", "newsletter", etc.)."""

        result = self.llm_client.run_sync(prompt)
        category_str = result.data.strip().lower()

        try:
            return EmailCategory(category_str)
        except ValueError:
            return EmailCategory.OTHER

    @final
    @property
    def _company_emails() -> dict[str, str]:
        """Mapping of email domains to company names.

        :return: Dictionary mapping email domains to company names.
        """
        return {
            "amazon.com": "Amazon",
            "ebay.com": "eBay",
            "walmart.com": "Walmart",
            "target.com": "Target",
            "bestbuy.com": "Best Buy",
        }

    def _convert_email_to_markdown(self, email: Email) -> str:
        """Convert email HTML body to markdown and redact PII.

        Uses html-to-markdown for conversion, then runs PII redaction
        to remove sensitive information before further processing.

        :param email: The email to convert.
        :return: PII-redacted markdown content.
        """
        markdown_content = convert_to_markdown(email.body.html or email.body.text or "")
        redacted_content = self.pii_redactor.redact_pii(markdown_content)
        return redacted_content

    def _categorize_email_subject(self, subject: str) -> EmailCategory:
        """Categorize an email based on subject line keywords.

        Checks for patterns like "order confirmed", "receipt", "invoice",
        and "newsletter" to determine the category.

        :param subject: The email subject line.
        :return: The determined email category.
        """
        subject_lower = subject.lower()

        is_order_confirmed = re.search(r"order #\d+ confirmed", subject_lower)
        if is_order_confirmed or "receipt" in subject_lower:
            return EmailCategory.RECEIPT
        elif "invoice" in subject_lower:
            return EmailCategory.INVOICE
        elif "newsletter" in subject_lower:
            return EmailCategory.NEWSLETTER
        else:
            return EmailCategory.UNKNOWN

    def _categorize_amazon_email(self, email: Email) -> EmailCategory:
        """Categorize an Amazon email based on sender address.

        :param email: The Amazon email to categorize.
        :return: The determined email category.
        """
        # Placeholder for Amazon-specific categorization logic
        if email.from_ == "auto-confirm@amazon.com":
            # Process Amazon purchase confirmation emails
            return EmailCategory.RECEIPT

    def _find_company_from_email(self, from_email: str) -> str | None:
        """Look up the company name from the sender's email domain.

        :param from_email: The sender's email address.
        :return: The company name if found, None otherwise.
        """
        email_domain = from_email.split("@")[-1]
        if email_domain not in self._company_emails():
            return None
        return self._company_emails[email_domain]
