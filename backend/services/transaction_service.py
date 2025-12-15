from collections import Counter
from typing import List

from models.budget import Transaction
from clients.ynab_client import YNABClient

class TransactionService:
    def __init__(self, ynab_client: YNABClient) -> None:
        self.ynab_client = ynab_client

    def get_uncategorized_transactions(self, from_date: str | None) -> List[Transaction]:
        return self.ynab_client.get_uncategorized_transactions()

    def categorize_transaction(self, transaction: Transaction, category_id: str) -> None:
        transaction.category_id = category_id
        self.ynab_client.categorize_transaction(
            transaction=transaction,
        )

    def get_transactions_by_payee(self, payee_id: str) -> List[Transaction]:
        results = []
        return results

    def determine_category_for_payee(self, payee_id: str) -> str | None:
        """Determines the category for a given payee based on historical transactions.
        If there are multiple categories or no categories, returns None. Otherwise, returns the single category ID.
        """
        transactions = self.ynab_client.get_transactions_by_payee_id(payee_id=payee_id)
        categorized_approved_transactions = [
            t for t in transactions if t.approved and t.category_id is not None
        ]

        sorted_transactions = sorted(categorized_approved_transactions, key=lambda t: t.date or "", reverse=True)
        category_count = Counter(list(map(lambda t: t.category_id, sorted_transactions)))

        category_ids = list(category_count.keys())

        if len(category_ids) == 1:
            return category_ids[0]
