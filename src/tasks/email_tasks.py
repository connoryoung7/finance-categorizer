from src.tasks import app


@app.task
def process_email(email_id: str) -> None:
    """Process a single email by ID."""
    # TODO: Inject dependencies and delegate to EmailIngestionService
    pass


@app.task
def ingest_emails_by_date_range(start_date: str, end_date: str) -> None:
    """Ingest emails within a date range."""
    # TODO: Inject dependencies and delegate to EmailIngestionService
    pass
