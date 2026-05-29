import pytest

from app.services.readiness import ReadinessService


@pytest.mark.asyncio
async def test_readiness_ok(monkeypatch, settings):
    class Conn:
        async def execute(self, _):
            return None

    class Ctx:
        async def __aenter__(self):
            return Conn()

        async def __aexit__(self, *args):
            return None

    class Engine:
        def connect(self):
            return Ctx()

    async def _ping(_settings):
        return None

    class _Q:
        def __init__(self, _settings):
            pass

        async def ensure_collection(self):
            return None

    monkeypatch.setattr("app.services.readiness.ping_redis", _ping)
    monkeypatch.setattr("app.services.readiness.QdrantCollectionService", _Q)

    report = await ReadinessService(Engine(), settings).check()
    assert report.postgres == "ok"
    assert report.redis == "ok"
    assert report.qdrant == "ok"
