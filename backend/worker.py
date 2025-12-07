import schedule

from clients.ynab_client import YNABClient
from config import settings
from services.ynab_service import YNABService
from agents.categorize_transaction_agent import CategorizeTransactionAgent

def main():
    ynab_client = YNABClient(access_token=settings.ynab_access_key)
    ynab_service = YNABService(ynab_client=ynab_client)
    categorize_transaction_agent = CategorizeTransactionAgent(ynab_service=ynab_service)

def categorize_latest_transactions(
    categorize_transaction_agent: CategorizeTransactionAgent
):
    transactions = ynab_service.get_transactions()

    for t in transactions:
        if not t.category_id:
            categorize_transaction_agent.categorize_transaction(transaction=t)
    

if __name__ == "__main__":
    schedule.every(1).day.do(main)
    
    while True:
        schedule.run_pending()
        time.sleep(120)
