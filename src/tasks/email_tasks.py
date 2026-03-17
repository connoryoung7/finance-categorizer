from src.agents.email_processor import EmailProcessor
from src.models.budget import Transaction
from src.tasks import app

email_processor = EmailProcessor()


@app.task
def process_email(email_id: str) -> None:
    """
    Have the EmailProcessor agent process a single email by ID.

    Args:
        email_id: The unique identifier of the email to process.
    Returns:
        None
    """
    email_processor.process_email(email_id)


@app.task
def ingest_emails_by_date_range(start_date: str, end_date: str) -> None:
    """Ingest emails within a date range."""
    # TODO: Inject dependencies and delegate to EmailIngestionService
    pass


@app.task
def send_transaction_alert(to_email: str, transaction_data: dict) -> None:
    """Send a transaction alert email for the given transaction."""
    from src.dependencies import get_email_service

    service = get_email_service()
    service.send_transaction_email(
        to_email=to_email, transaction=Transaction(**transaction_data)
    )
