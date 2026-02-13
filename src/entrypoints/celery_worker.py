# Re-export Celery app for: celery -A src.entrypoints.celery_worker worker
from src.tasks import app  # noqa: F401
