from celery.schedules import crontab
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    ynab_access_key: str
    ynab_budget_id: str
    mistral_access_key: str
    nylas_api_key: str
    nylas_api_uri: str
    nylas_client_id: str
    nylas_grant_id: str
    nylas_webhook_secret: str

    # Database settings
    database_url: str = (
        "postgresql://postgres:postgres@localhost:5432/finance_categorizer"
    )

    # Celery settings
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # SMTP settings
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_from_address: str = ""


settings = Settings()


class CelerySettings:
    """Celery configuration loaded from Settings."""

    def __init__(self) -> None:
        self.broker_url = settings.celery_broker_url
        self.result_backend = settings.celery_result_backend
        self.task_serializer = "json"
        self.result_serializer = "json"
        self.accept_content = ["json"]
        self.timezone = "UTC"
        self.enable_utc = True
        self.beat_schedule = {
            "sync-ynab-transactions": {
                "task": "src.tasks.transaction_tasks.sync_ynab_transactions",
                "schedule": crontab(minute=0, hour="*/6"),
            },
        }


celery_settings = CelerySettings()
