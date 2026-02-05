from abc import ABC, abstractmethod
from typing import List

from src.models.budget import Payee, Transaction


class TransactionServiceInterface(ABC):
    """Abstract base class for transaction service implementations."""

    @abstractmethod
    def get_uncategorized_transactions(
        self,
        from_date: str | None = None,
    ) -> List[Transaction]:
        """
        Get all uncategorized transactions.

        Args:
            from_date: Optional start date filter (ISO format).

        Returns:
            List of uncategorized transactions.
        """
        pass

    @abstractmethod
    def categorize_transaction(
        self,
        transaction: Transaction,
        category_id: str,
    ) -> None:
        """
        Categorize a transaction.

        Args:
            transaction: The transaction to categorize.
            category_id: The category ID to assign.
        """
        pass

    @abstractmethod
    def get_transactions_by_payee(self, payee_id: str) -> List[Transaction]:
        """
        Get all transactions for a specific payee.

        Args:
            payee_id: The payee ID to filter by.

        Returns:
            List of transactions for the payee.
        """
        pass

    @abstractmethod
    def determine_category_for_payee(self, payee_id: str) -> str | None:
        """
        Determine the category for a payee based on historical transactions.

        Args:
            payee_id: The payee ID to analyze.

        Returns:
            Category ID if a single category is found, None otherwise.
        """
        pass

    @abstractmethod
    def get_payees(self) -> List[Payee]:
        """
        Get all payees.

        Returns:
            List of all payees.
        """
        pass
