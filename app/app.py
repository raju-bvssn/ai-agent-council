"""
FastAPI application for Agent Council system.

Main application factory and configuration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import get_api_router
from app.utils.logging import configure_logging, get_logger
from app.utils.settings import get_settings

# Configure logging on module import
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("application_starting")
    settings = get_settings()
    logger.info(
        "application_configured",
        env=settings.env,
        debug=settings.debug,
        demo_mode=settings.demo_mode,
        api_host=settings.api_host,
        api_port=settings.api_port,
        api_base_url=settings.api_base_url,
        allowed_origins=settings.get_allowed_origins_list(),
    )

    yield

    # Shutdown
    logger.info("application_shutting_down")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI app
    """
    settings = get_settings()

    app = FastAPI(
        title="Agent Council API",
        description="Multi-agent orchestration system for Salesforce Professional Services",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    api_router = get_api_router()
    app.include_router(api_router, prefix="/api/v1")

    logger.info("fastapi_app_created")

    return app


# Create app instance
app = create_app()

