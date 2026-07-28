from abc import ABC, abstractmethod
import uuid

from src.models.order import Order


class OrderRepoInterface(ABC):
    """Abstract base class for order repository implementations."""

    @abstractmethod
    def upsert_order(self, order: Order) -> uuid.UUID:
        """Upsert an order and replace its line items.

        The order is upserted in place on its ``(transaction_id, order_number)``
        idempotency key, and its line items are deleted and re-inserted every
        call. Both happen inside a single transaction.

        Args:
            order: The Order domain model to persist.

        Returns:
            The stable UUID of the persisted order.
        """
        pass
