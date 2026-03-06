from nylas import Client
from nylas.models.messages import Message

from src.interfaces.email_searcher import (
    EmailSearcher,
    EmailSearchQuery,
    EmailSearchResult,
)
from src.models.email import Email, RawBody


class NylasEmailClient(EmailSearcher):
    """
    The client that leverages the Nylas API to search for emails based on
    specific queries.
    """

    def __init__(self, api_key: str, api_uri: str, grant_id: str):
        self.client = Client(
            api_key=api_key,
            api_uri=api_uri,
        )
        self.grant_id = grant_id

    def search_emails(self, query: EmailSearchQuery) -> EmailSearchResult:
        response = self.client.messages.list(
            identifier=self.grant_id,
            query_params=self._format_search_query(query),
        )

        return EmailSearchResult(data=self._format_nylas_emails(response.data))

    def _format_search_query(self, query: EmailSearchQuery) -> dict:
        # query_dict = query.model_dump(exclude_none=True)
        query_dict = {}
        if query.start_date:
            query_dict["received_before"] = query.end_date
        if query.end_date:
            query_dict["received_after"] = query.start_date

        print(f"Formatted search query: {query_dict}")
        return query_dict

    def _format_nylas_emails(self, nylas_emails: list[Message]) -> list[Email]:
        return list(
            map(
                lambda ne: Email(
                    **{
                        "from": ne.from_[0].get("email") if ne.from_ else "",
                        "to": [recipient.get("email") for recipient in ne.to]
                        if ne.to
                        else [],
                        "subject": ne.subject or "",
                        "body": RawBody(html=ne.body),
                        "received_at": ne.date,
                    }
                ),
                nylas_emails,
            )
        )
