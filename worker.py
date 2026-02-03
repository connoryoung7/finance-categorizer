from mistralai import Mistral

from agents.transaction_categorizer_agent import CategorizeTransactionAgent
from clients.ynab_client import YNABClient
from config import settings
from services.transaction_service import TransactionService as YNABService


def main():
    ynab_client = YNABClient(access_token=settings.ynab_access_key, budget_id=settings.ynab_budget_id)
    ynab_service = YNABService(ynab_client=ynab_client)
    mistral_llm = Mistral(api_key=settings.mistral_access_key)

    categories = ynab_client.get_categories()
    categorize_transaction_agent = CategorizeTransactionAgent(llm_client=mistral_llm, transaction_service=ynab_service, categories=categories)

    uncategorized_transactions = ynab_client.get_uncategorized_transactions()[0:3]
    print(f"Found {len(uncategorized_transactions)} uncategorized transactions")

    for t in uncategorized_transactions:
        categorize_transaction_agent.categorize_transaction(transaction=t)
        

def categorize_latest_transactions(
    categorize_transaction_agent: CategorizeTransactionAgent,
    ynab_service: YNABService,
):
    print("Searching for uncategorized transactions")
    transactions = ynab_service.get_uncategorized_transactions(from_date=None)

    print(f"Found {len(transactions)} uncategorized transactions")

    for t in transactions:
        if not t.category_id:
            categorize_transaction_agent.categorize_transaction(transaction=t)
            break
    
def generate_payee_categorizations(
    categorize_transaction_agent: CategorizeTransactionAgent,
    ynab_service: YNABService,
):
    for payee in ynab_service.get_payees():
        # Check if we have a categorization for this payee
        ynab_service.determine_category_for_payee(payee_id=payee.id)

if __name__ == "__main__":
    main()
