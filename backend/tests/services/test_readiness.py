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


@pytest.mark.asyncio
async def test_readiness_skips_redis_when_async_ingestion_disabled(
    settings, monkeypatch
):
    settings.USE_ASYNC_INGESTION = False
    called = {"redis": False}

    async def fake_ping(settings):
        called["redis"] = True

    monkeypatch.setattr("app.services.readiness.ping_redis", fake_ping)

    class Q:
        def __init__(self, settings):
            pass

        async def ensure_collection(self):
            pass

    monkeypatch.setattr("app.services.readiness.QdrantCollectionService", Q)

    class FakeConn:
        async def execute(self, _):
            return None

    class FakeCtx:
        async def __aenter__(self):
            return FakeConn()

        async def __aexit__(self, *args):
            return None

    class FakeEngine:
        def connect(self):
            return FakeCtx()

    await ReadinessService(engine=FakeEngine(), settings=settings).check()
    assert called["redis"] is False
