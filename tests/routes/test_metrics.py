from fastapi.testclient import TestClient

from src.entrypoints.api import app

client = TestClient(app)


def test_metrics_endpoint_returns_200():
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_content_type_is_prometheus_text():
    response = client.get("/metrics")
    assert "text/plain" in response.headers["content-type"]


def test_metrics_body_contains_http_requests_total():
    client.get("/health")
    response = client.get("/metrics")
    assert "http_requests_total" in response.text
