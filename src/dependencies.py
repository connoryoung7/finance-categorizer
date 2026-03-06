from functools import lru_cache

from sqlalchemy import Engine, create_engine

from src.clients.ynab_client import YNABClient
from src.config import settings
from src.repos.transaction_postgres_repo import TransactionPostgresRepo
from src.services.sync_service import SyncService
from src.services.transaction_service import TransactionService


@lru_cache
def get_ynab_client() -> YNABClient:
    return YNABClient(
        access_token=settings.ynab_access_key, budget_id=settings.ynab_budget_id
    )


@lru_cache
def get_transaction_service() -> TransactionService:
    client = get_ynab_client()
    return TransactionService(ynab_client=client)


@lru_cache
def get_db_engine() -> Engine:
    return create_engine(settings.database_url)


@lru_cache
def get_transaction_repo() -> TransactionPostgresRepo:
    engine = get_db_engine()
    return TransactionPostgresRepo(db=engine)


@lru_cache
def get_sync_service() -> SyncService:
    return SyncService(
        ynab_client=get_ynab_client(),
        transaction_repo=get_transaction_repo(),
        budget_id=settings.ynab_budget_id,
    )
