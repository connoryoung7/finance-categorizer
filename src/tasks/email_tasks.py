from src.agents.email_processor import EmailProcessor
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
