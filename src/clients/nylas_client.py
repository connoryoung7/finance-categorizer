
from nylas import Client
from nylas.models.messages import Message

from src.interfaces.email_searcher import (
    EmailSearcher,
    EmailSearchQuery,
    EmailSearchResult,
)
from src.models.email import Email


class NylasEmailClient(EmailSearcher):
    """
    The client that leverages the Nylas API to search for emails based on specific queries.
    """
    def __init__(self, api_key: str, api_uril: str, grant_id: str):
        self.client = Client(
            api_key=api_key,
            api_uri=api_uril,
        )
        self.grant_id = grant_id

    def search_emails(self, query: EmailSearchQuery) -> EmailSearchResult:
        response = self.client.messages.list(
            identifier=self.grant_id,
            query_params=query.model_dump(exclude_none=True),
        )

        return EmailSearchResult(data=self._format_nylas_emails(response.data))
    
    def _format_nylas_emails(self, nylas_emails: list[Message]) -> list[Email]:
        return list(
            map(
                lambda ne: Email(
                    id=ne.id,
                    from_=ne.from_[0].get("email") if ne.from_ else "",
                    to=[recipient.get("email") for recipient in ne.to] if ne.to else [],
                    subject=ne.subject or "",
                    content=ne.body or "",
                ),
                nylas_emails
            )
        )
