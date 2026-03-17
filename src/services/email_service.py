from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
import smtplib

from jinja2 import Template
from mjml import mjml2html

from src.config import settings
from src.interfaces.email_sender import EmailSender
from src.logger import logger
from src.models.budget import Transaction

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"


class EmailService(EmailSender):
    """Service for sending formatted HTML emails."""

    def __init__(self):
        super().__init__()

    def _load_template(self, template_name: str) -> str:
        """Load an MJML template from the templates directory."""
        template_path = TEMPLATES_DIR / f"{template_name}.mjml"
        return template_path.read_text()

    def _render_template(self, template_content: str, **kwargs) -> str:
        """Render a Jinja2 template with the given variables."""
        template = Template(template_content)
        return template.render(**kwargs)

    def _compile_mjml(self, mjml_content: str) -> str:
        """Compile MJML to HTML."""
        return mjml2html(mjml_content)

    def _format_amount(self, amount: int) -> str:
        """Format amount from milliunits to dollars."""
        dollars = amount / 1000
        return f"${dollars:,.2f}"

    def send_transaction_email(self, to_email: str, transaction: Transaction) -> None:
        """Send a transaction alert email."""
        mjml_template = self._load_template("transaction_alert")

        rendered_mjml = self._render_template(
            mjml_template,
            amount=self._format_amount(transaction.amount),
            merchant=transaction.payee_name or "Unknown",
            category=transaction.category_name or "Uncategorized",
            date=transaction.date or "Unknown",
        )

        html_content = self._compile_mjml(rendered_mjml)

        self._send_email(
            to_email=to_email,
            subject="New Transaction Alert",
            html_content=html_content,
        )

    def _send_email(self, to_email: str, subject: str, html_content: str) -> None:
        """Send an email via SMTP."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.email_from_address
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.email_from_address, to_email, msg.as_string())
            logger.info(f"Email sent to {to_email} with subject: {subject}")
