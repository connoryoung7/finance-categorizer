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
    def find_candidate_transactions(
        self,
        amount_milliunits: int,
        date: str | None = None,
        window_days: int = 7,
        payee_hint: str | None = None,
    ) -> list[Transaction]:
        """Find transactions that could correspond to a given charge.

        YNAB records outflows as negative milliunits while invoice totals are
        positive, so matching is done on absolute value.

        Args:
            amount_milliunits: The charge amount; sign is ignored.
            date: ISO 8601 invoice date to centre the search window on. When
                None, the window is not applied.
            window_days: How many days either side of ``date`` to consider.
            payee_hint: Vendor name to narrow on, matched case-insensitively
                as a substring of the payee name.

        Returns:
            Matching transactions, excluding deleted ones. Ordering is not
            significant -- ranking is the matching service's job.
        """
        pass

    @abstractmethod
    def get_transaction(self, transaction_id: str) -> Transaction | None:
        """Fetch a single transaction by id, or None if it does not exist."""
        pass

    @abstractmethod
    def update_sync_state(self, budget_id: str, server_knowledge: int) -> None:
        """Update the sync state after a successful sync.

        Args:
            budget_id: The YNAB budget ID.
            server_knowledge: The new server knowledge value from YNAB.
        """
        pass
