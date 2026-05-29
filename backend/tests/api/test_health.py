import pytest


@pytest.mark.asyncio
async def test_health_liveness(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ready_reports_dependencies(async_client, monkeypatch):
    class R:
        postgres = "ok"
        redis = "ok"
        qdrant = "ok"

    async def _check(self):
        return R()

    monkeypatch.setattr("app.api.v1.health.ReadinessService.check", _check)
    response = await async_client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "dependencies": {"postgres": "ok", "redis": "ok", "qdrant": "ok"},
    }
