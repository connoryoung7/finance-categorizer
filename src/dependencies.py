from functools import lru_cache

from pydantic_ai import Agent
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.mistral import MistralProvider
from sqlalchemy import Engine, create_engine

from src.adapters.docling_document_parser import DoclingDocumentParser
from src.adapters.presidio_pii_redactor import PresidioPIIRedactor
from src.agents.invoice_extractor_agent import (
    INVOICE_EXTRACTION_SYSTEM_PROMPT,
    InvoiceExtractorAgent,
)
from src.clients.ynab_client import YNABClient
from src.config import settings
from src.repos.invoice_upload_postgres_repo import InvoiceUploadPostgresRepo
from src.repos.order_postgres_repo import OrderPostgresRepo
from src.repos.transaction_postgres_repo import TransactionPostgresRepo
from src.services.email_service import EmailService
from src.services.order_ingestion_service import OrderIngestionService
from src.services.order_matching_service import OrderMatchingService
from src.services.sync_service import SyncService
from src.services.transaction_service import TransactionService


@lru_cache
def get_ynab_client() -> YNABClient:
    return YNABClient(
        access_token=settings.ynab_access_key, budget_id=settings.ynab_budget_id
    )


@lru_cache
def get_transaction_service() -> TransactionService:
    client = get_ynab_client()
    return TransactionService(ynab_client=client)


@lru_cache
def get_db_engine() -> Engine:
    return create_engine(settings.database_url)


@lru_cache
def get_transaction_repo() -> TransactionPostgresRepo:
    engine = get_db_engine()
    return TransactionPostgresRepo(db=engine)


@lru_cache
def get_order_repo() -> OrderPostgresRepo:
    engine = get_db_engine()
    return OrderPostgresRepo(db=engine)


@lru_cache
def get_invoice_upload_repo() -> InvoiceUploadPostgresRepo:
    engine = get_db_engine()
    return InvoiceUploadPostgresRepo(db=engine)


@lru_cache
def get_pii_redactor() -> PresidioPIIRedactor:
    return PresidioPIIRedactor()


@lru_cache
def get_document_parser() -> DoclingDocumentParser:
    # Loads models on construction, so it is built once and reused.
    return DoclingDocumentParser()


@lru_cache
def get_invoice_extractor() -> InvoiceExtractorAgent:
    model = MistralModel(
        settings.invoice_extraction_model,
        provider=MistralProvider(api_key=settings.mistral_access_key),
    )
    return InvoiceExtractorAgent(
        llm_client=Agent(
            model, system_prompt=INVOICE_EXTRACTION_SYSTEM_PROMPT
        ),
        pii_redactor=get_pii_redactor(),
    )


@lru_cache
def get_order_matching_service() -> OrderMatchingService:
    return OrderMatchingService(transaction_repo=get_transaction_repo())


@lru_cache
def get_order_ingestion_service() -> OrderIngestionService:
    return OrderIngestionService(order_repo=get_order_repo())


@lru_cache
def get_email_service() -> EmailService:
    return EmailService()


@lru_cache
def get_sync_service() -> SyncService:
    return SyncService(
        ynab_client=get_ynab_client(),
        transaction_repo=get_transaction_repo(),
        budget_id=settings.ynab_budget_id,
    )
