from nylas import Client

from clients.interfaces.email_searcher import (
    EmailSearcher,
    EmailSearchQuery,
    EmailSearchResult,
)


class NylasEmailClient(EmailSearcher):
    def __init__(self, api_key: str, api_uril: str, grant_id: str):
        self.client = Client(
            api_key=api_key,
            api_uri=api_uril,
        )
        self.grant_id = grant_id

    def get_emails(self, filters: EmailSearchQuery) -> EmailSearchResult:
        return EmailSearchResult(data=[])
