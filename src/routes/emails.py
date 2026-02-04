

from fastapi import APIRouter


def create_email_routes() -> APIRouter:
    routes = APIRouter(
        prefix="/webhooks/emails",
        tags=["emails", "webhooks"],
    )

    return routes
