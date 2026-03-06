import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from src.config import settings
from src.tasks.email_tasks import process_email

webhooks: list[Any] = []


class EmailObject(BaseModel):
    id: str
    grant_id: str
    subject: str | None = None
    body: str | None = None


class WebhookEvent(BaseModel):
    specversion: str
    type: str
    source: str
    id: str
    time: str
    data: dict


def verify_signature(message: bytes, key: str, signature: str | None) -> bool:
    """Verify the Nylas webhook signature."""
    if not signature or not key:
        return False
    digest = hmac.new(key.encode(), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


def store_event_json(event: WebhookEvent) -> None:
    """Store the raw event JSON for later processing."""
    # TODO: Implement persistent storage
    pass


def create_email_routes() -> APIRouter:
    routes = APIRouter(
        prefix="/webhooks/emails",
        tags=["emails", "webhooks"],
    )

    @routes.post("/nylas")
    async def webhook(
        request: Request,
        event: WebhookEvent | None = None,
        x_nylas_signature: str | None = Header(None),
    ):
        if request.method == "GET":
            challenge = request.query_params.get("challenge")
            if challenge:
                return PlainTextResponse(challenge)
            return PlainTextResponse(
                "No challenge", status_code=status.HTTP_400_BAD_REQUEST
            )
        # POST method
        body = await request.body()
        is_genuine = verify_signature(
            message=body,
            key=settings.nylas_webhook_secret,
            signature=x_nylas_signature,
        )
        if not is_genuine:
            return PlainTextResponse("Signature verification failed!", status_code=401)

        # Store the raw event JSON
        if event:
            store_event_json(event)
            email_obj = EmailObject(**event.data["object"])
            process_email.delay(email_obj.id)
        else:
            return PlainTextResponse("No event data", status_code=400)

        webhooks.append(email_obj)
        return PlainTextResponse("Webhook received", status_code=200)

    return routes
