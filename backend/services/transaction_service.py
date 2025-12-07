from abc import ABC, abstractmethod
from typing import List

from models.budget import Transaction

class ITransactionService(ABC):
    @abstractmethod
    def get_transactions(from_date: str | None) -> List[Transaction]:
        pass

    @abstractmethod
    def categorize_transaction(transaction_id: str, category_id: str):
        pass

    @abstractmethod
    def get_transactions_by_payee(payee_id: str) -> List[Transaction]:
        pass
