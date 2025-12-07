from clients.ynab_client import YNABClient
from config import settings
from services.ynab_service import YNABService

def main():
    ynab_client = YNABClient(access_token=settings.ynab_access_key)
    ynab_service = YNABService(ynab_client=ynab_client)

    transactions = ynab_service.get_transactions()

    for t in transactions:
        if not t.category_id:
            # Need to categorize this transaction
            pass

def categorize_latest_transactions():
    

if __name__ == "__main__":
    main()
