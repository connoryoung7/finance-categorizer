from src.tasks import app


@app.task
def categorize_transaction(transaction_id: str) -> None:
    """Categorize a single transaction by ID."""
    # TODO: Inject dependencies and delegate to TransactionService
    pass


@app.task
def categorize_uncategorized_transactions() -> None:
    """Find and categorize all uncategorized transactions."""
    # TODO: Inject dependencies and delegate to TransactionService
    pass
