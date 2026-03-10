from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.redis import close_redis, get_redis

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting VIPCam backend...")

    # Initialize Redis
    await get_redis()
    logger.info("Redis connected")

    # Start pipeline if enabled
    if settings.enable_pipeline:
        from app.pipeline.manager import pipeline_manager

        await pipeline_manager.start()
        logger.info("Processing pipeline started")

    yield

    # Shutdown
    if settings.enable_pipeline:
        from app.pipeline.manager import pipeline_manager

        await pipeline_manager.stop()
        logger.info("Processing pipeline stopped")

    await close_redis()
    logger.info("VIPCam backend shut down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="VIPCam - Barbearia VIP Face Analytics",
        description="Real-time facial analysis system for Barbearia VIP franchise units",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.router import api_router

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
