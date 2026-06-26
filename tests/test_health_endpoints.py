from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import HealthCheckResult


client = TestClient(app)


def _healthy_result(service: str) -> HealthCheckResult:
    return HealthCheckResult(
        service=service,
        ok=True,
        status="healthy",
        checked_at=datetime.now(timezone.utc),
        response_time_ms=1.0,
        details={"source": "test"},
    )


def test_root_lists_dify_tool_metadata() -> None:
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["openapi"] == "/openapi.json"
    assert payload["dify_openapi"] == "/dify-openapi.json"
    assert "/health/docker" in payload["health_endpoints"]


def test_docs_page_is_local_and_does_not_use_cdn() -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "inner-ai-tools API 文档" in response.text
    assert "https://cdn.jsdelivr.net" not in response.text
    assert "/openapi.json" in response.text


def test_dify_openapi_schema_is_compatible_with_dify() -> None:
    response = client.get("/dify-openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert payload["openapi"] == "3.0.3"
    assert payload["servers"][0]["url"] == "http://192.168.1.103:8000"
    assert "/" not in payload["paths"]
    assert "/health/docker" in payload["paths"]
    assert payload["paths"]["/health/docker"]["get"]["operationId"] == "checkDockerHealth"


@pytest.mark.parametrize(
    ("path", "function_name", "service"),
    [
        ("/health/docker", "check_docker", "docker"),
        ("/health/ollama", "check_ollama", "ollama"),
        ("/health/dify", "check_dify", "dify"),
        ("/health/milvus", "check_milvus", "milvus"),
    ],
)
def test_health_endpoint_routes(monkeypatch: pytest.MonkeyPatch, path: str, function_name: str, service: str) -> None:
    async def fake_check(_settings):
        return _healthy_result(service)

    monkeypatch.setattr(f"app.main.{function_name}", fake_check)

    response = client.get(path)

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == service
    assert payload["ok"] is True
    assert payload["status"] == "healthy"
