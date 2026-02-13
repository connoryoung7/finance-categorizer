from functools import lru_cache

from src.clients.ynab_client import YNABClient
from src.config import settings
from src.services.transaction_service import TransactionService


@lru_cache
def get_ynab_client() -> YNABClient:
    return YNABClient(
        access_token=settings.ynab_access_key,
        budget_id=settings.ynab_budget_id
    )


@lru_cache
def get_transaction_service() -> TransactionService:
    client = get_ynab_client()
    return TransactionService(ynab_client=client)
