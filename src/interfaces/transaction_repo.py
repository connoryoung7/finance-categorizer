from abc import ABC, abstractmethod

from src.models.budget import Transaction


class TransactionRepoInterface(ABC):
    """Abstract base class for transaction repository implementations."""

    @abstractmethod
    def upsert_transactions(self, transactions: list[Transaction]) -> int:
        """Upsert transactions into the database.

        Args:
            transactions: List of Transaction domain models to upsert.

        Returns:
            Number of transactions upserted.
        """
        pass

    @abstractmethod
    def get_last_knowledge_of_server(self, budget_id: str) -> int | None:
        """Retrieve the last known server knowledge for incremental sync.

        Args:
            budget_id: The YNAB budget ID.

        Returns:
            The server knowledge value, or None if no sync has occurred.
        """
        pass

    @abstractmethod
    def update_sync_state(self, budget_id: str, server_knowledge: int) -> None:
        """Update the sync state after a successful sync.

        Args:
            budget_id: The YNAB budget ID.
            server_knowledge: The new server knowledge value from YNAB.
        """
        pass
