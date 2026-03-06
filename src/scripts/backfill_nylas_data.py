from datetime import datetime

from src.clients.nylas_client import NylasEmailClient
from src.config import settings
from src.interfaces.email_searcher import EmailSearchQuery

nylas_email_client = NylasEmailClient(
    api_key=settings.nylas_api_key,
    api_uri=settings.nylas_api_uri,
    grant_id=settings.nylas_grant_id,
)

start_date = "2024-01-01"
end_date = "2024-12-31"


def backfill_nylas_data():
    emails = nylas_email_client.search_emails(
        query=EmailSearchQuery(
            limit=10,
            start_date=int(datetime.strptime(start_date, "%Y-%m-%d").timestamp()),
            end_date=int(datetime.strptime(end_date, "%Y-%m-%d").timestamp()),
        )
    )

    print(f"Found {len(emails.data)} emails to backfill.")
    print("Emails")
    for email in emails.data:
        print(f" - {email.subject} from {email.from_}: sent at {email.received_at}")


if __name__ == "__main__":
    backfill_nylas_data()
