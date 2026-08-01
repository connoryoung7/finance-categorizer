from loguru import logger

from src.dependencies import get_sync_service
from src.tasks import app
from src.tasks.invoice_tasks import retry_unmatched_invoices


@app.task(rate_limit="10/m")
def categorize_transaction(transaction_id: str) -> None:
    """Categorize a single transaction by ID."""
    # TODO: Inject dependencies and delegate to TransactionService
    pass


@app.task
def categorize_uncategorized_transactions() -> None:
    """Find and categorize all uncategorized transactions."""
    # TODO: Inject dependencies and delegate to TransactionService
    pass


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_ynab_transactions(self) -> dict:
    """Sync transactions from YNAB into the local database."""
    try:
        sync_service = get_sync_service()
        count = sync_service.sync_transactions()
        # Newly posted charges may be what an already-uploaded invoice was
        # waiting for, so give the unmatched ones another look.
        retry_unmatched_invoices.delay()
        return {"status": "success", "transactions_synced": count}
    except Exception as exc:
        logger.error(f"YNAB sync failed: {exc}")
        raise self.retry(exc=exc) from exc
