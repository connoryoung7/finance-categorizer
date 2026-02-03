from abc import ABC, abstractmethod
from datetime import time
from typing import List, Optional

from pydantic import BaseModel

from models.email import Email


class EmailSearchQuery(BaseModel):
    '''
    Filters for any query regarding searching on emails
    '''
    search_query_native: Optional[str] = None
    from_email: Optional[str] = None
    subject_contains: Optional[str] = None
    start_date: Optional[time] = None  # Unix timestamp
    end_date: Optional[time] = None    # Unix timestamp
    limit: Optional[int] = 100

class EmailSearchResult(BaseModel):
    data: List[Email]

class EmailSearcher(ABC):
    @abstractmethod
    def search_emails(self, query: EmailSearchQuery) -> EmailSearchResult:
        pass
