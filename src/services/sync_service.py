from loguru import logger

from src.clients.ynab_client import YNABClient
from src.interfaces.transaction_repo import TransactionRepoInterface


class SyncService:
    def __init__(
        self,
        ynab_client: YNABClient,
        transaction_repo: TransactionRepoInterface,
        budget_id: str,
    ) -> None:
        self.ynab_client = ynab_client
        self.transaction_repo = transaction_repo
        self.budget_id = budget_id

    def sync_transactions(self) -> int:
        """Sync transactions from YNAB into the local database.

        Returns:
            Number of transactions upserted.
        """
        last_knowledge = self.transaction_repo.get_last_knowledge_of_server(
            self.budget_id
        )

        logger.info(
            "Starting YNAB transaction sync "
            f"(budget={self.budget_id}, last_knowledge={last_knowledge})"
        )

        transactions, server_knowledge = self.ynab_client.get_transactions(
            last_knowledge_of_server=last_knowledge,
        )

        count = self.transaction_repo.upsert_transactions(transactions)

        self.transaction_repo.update_sync_state(self.budget_id, server_knowledge)

        logger.info(
            f"Sync complete: upserted {count} transactions "
            f"(server_knowledge={server_knowledge})"
        )

        return count
