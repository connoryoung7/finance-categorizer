from abc import ABC, abstractmethod

from backend.models.order import Order


class OrderCategorizer(ABC):
    @abstractmethod
    def format_order(self, order: str) -> Order | None:
        """
        Format the Markdown string from an email into an Order object.

        :param order: A string representing the order details.
        :return: An Order object if formatting is successful, otherwise None.
        """
        pass
