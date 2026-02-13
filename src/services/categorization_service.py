from src.agents.transaction_categorizer_agent import CategorizeTransactionAgent
from src.services.transaction_service import TransactionService


def categorize_latest_transactions(
    categorize_transaction_agent: CategorizeTransactionAgent,
    transaction_service: TransactionService,
):
    print("Searching for uncategorized transactions")
    transactions = transaction_service.get_uncategorized_transactions(from_date=None)

    print(f"Found {len(transactions)} uncategorized transactions")

    for t in transactions:
        if not t.category_id:
            categorize_transaction_agent.categorize_transaction(transaction=t)
            break


def generate_payee_categorizations(
    transaction_service: TransactionService,
):
    for payee in transaction_service.get_payees():
        transaction_service.determine_category_for_payee(payee_id=payee.id)
