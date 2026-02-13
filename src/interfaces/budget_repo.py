from abc import ABC, abstractmethod

from src.models.budget import PayeeCategorization


class BudgetRepoInterface(ABC):
    """Abstract base class for budget repository implementations."""

    @abstractmethod
    def get_payee_categorization(self, payee_id: str) -> PayeeCategorization | None:
        """
        Retrieve budget data from the database.

        Args:
            payee_id: The payee ID to look up.

        Returns:
            PayeeCategorization if found, None otherwise.
        """
        pass

    @abstractmethod
    def create_payee_categorization(
        self,
        payee_id: str,
        category_id: str,
        status: str,
    ) -> None:
        """
        Create a new budget entry in the database.

        Args:
            payee_id: The payee ID.
            category_id: The category ID to assign.
            status: The categorization status.
        """
        pass

    @abstractmethod
    def update_payee_categorization(
        self,
        payee_id: str,
        category_id: str,
        status: str,
    ) -> None:
        """
        Update an existing budget entry in the database.

        Args:
            payee_id: The payee ID.
            category_id: The category ID to assign.
            status: The categorization status.
        """
        pass
