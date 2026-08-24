"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Medium Article Agent",
        description="Agentic Medium Article Generator — LangGraph editorial pipeline",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        sg = settings.style_guide_status()
        return {
            "status": "ok",
            "style_guide": sg,
            "llm_provider": settings.llm_provider,
        }

    # Routers added in later phases
    try:
        from app.api.routes_pipeline import router as pipeline_router
        app.include_router(pipeline_router, prefix="/api/pipeline", tags=["pipeline"])
    except ImportError:
        pass

    try:
        from app.api.routes_export import router as export_router
        app.include_router(export_router, prefix="/api/export", tags=["export"])
    except ImportError:
        pass

    try:
        from app.api.routes_stream import router as stream_router
        app.include_router(stream_router, prefix="/api/stream", tags=["stream"])
    except ImportError:
        pass

    return app


app = create_app()
