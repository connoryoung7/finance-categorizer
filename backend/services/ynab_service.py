from clients.ynab_client import YNABClient
from services.transaction_service import ITransactionService

class YNABService(ITransactionService):
    def __init__(self, ynab_client: YNABClient):
        self.ynab_client = ynab_client

    def get_transactions(from_date):
        if not from_date:
            from_date = "1970-01-01"

        return super().get_transactions()

    def categorize_transaction(transaction_id, category_id):
        return super().categorize_transaction(category_id)
    
    def get_transactions_by_payee(payee_id):
        return super().get_transactions_by_payee()
