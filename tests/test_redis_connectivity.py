import os

from celery import Celery
import pytest
import redis as redis_lib

REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")


@pytest.fixture
def redis_client():
    client = redis_lib.from_url(REDIS_URL)
    yield client
    client.close()


def test_api_redis_connectivity(redis_client):
    """Verify the API can connect to the Redis instance."""
    assert redis_client.ping() is True


def test_worker_redis_connectivity():
    """Verify the Celery worker can connect to its Redis broker."""
    app = Celery(broker=REDIS_URL)
    conn = app.connection()
    conn.ensure_connection(max_retries=3)
    conn.close()
