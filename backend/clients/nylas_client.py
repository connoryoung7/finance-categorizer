from dataclasses import dataclass
from typing import List

from clients.interfaces.email_searcher import EmailSearchQuery, EmailSearchResult, EmailSearcher
from models.email import Email


class NylasEmailClient(EmailSearcher):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_emails(self, filters: EmailSearchQuery) -> EmailSearchResult:
        # Placeholder implementation
        # In a real implementation, this would interact with the Nylas API
        return EmailSearchResult(data=[])
