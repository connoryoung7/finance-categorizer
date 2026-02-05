from abc import ABC, abstractmethod
from datetime import time

from pydantic import BaseModel

from src.models.email import Email


class EmailSearchQuery(BaseModel):
    '''
    Filters for any query regarding searching on emails
    '''
    search_query_native: str | None = None
    from_email: str | None = None
    subject_contains: str | None = None
    start_date: time | None = None  # Unix timestamp
    end_date: time | None = None    # Unix timestamp
    limit: int | None = 100

class EmailSearchResult(BaseModel):
    data: list[Email]

class EmailSearcher(ABC):
    @abstractmethod
    def search_emails(self, query: EmailSearchQuery) -> EmailSearchResult:
        pass
