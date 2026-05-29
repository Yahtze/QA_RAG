from fastapi import APIRouter, Depends

from app.api.deps import get_settings_dep
from app.core.config import Settings
from app.db.session import engine
from app.services.readiness import ReadinessService

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(settings: Settings = Depends(get_settings_dep)):
    report = await ReadinessService(engine, settings).check()
    return {
        "status": "ok",
        "dependencies": {
            "postgres": report.postgres,
            "redis": report.redis,
            "qdrant": report.qdrant,
        },
    }
