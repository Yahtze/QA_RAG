from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_settings_dep
from app.api.v1.api import api_router
from app.api.v1.health import router as health_router
from app.db.session import engine
from app.services.qdrant_collection import QdrantCollectionService
from app.services.readiness import ReadinessService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings_dep()
    await QdrantCollectionService(settings).ensure_collection()
    await ReadinessService(engine, settings).check()
    yield


def create_app() -> FastAPI:
    settings = get_settings_dep()
    app = FastAPI(title="QA RAG Backend", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(api_router)
    return app


app = create_app()
