"""
FastAPI Application Factory.

Creates and configures the FastAPI application.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from scout.core import get_logger, settings, setup_logging
from scout.core.exceptions import ScoutError
from scout.infrastructure.api.v1 import router as api_v1_router
from scout.infrastructure.api.middleware import (
    scout_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
)
from scout.modules import register_default_modules

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Runs on startup and shutdown.
    """
    # --- Startup ---
    setup_logging()
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    # Register default modules
    register_default_modules()
    logger.info("modules_registered")

    # Initialize database connection
    try:
        from scout.infrastructure.database import init_db
        await init_db()
    except Exception as e:
        logger.warning("database_init_skipped", reason=str(e))

    # Start Supervisor Agent
    try:
        from scout.agents.supervisor import supervisor
        await supervisor.start()
        logger.info("supervisor_started")
    except Exception as e:
        logger.error("supervisor_start_failed", error=str(e))

    # Start Learning Engine
    try:
        from scout.agents.learning_engine import learning_engine
        await learning_engine.start()
        logger.info("learning_engine_started_lifecycle")
    except Exception as e:
        logger.error("learning_engine_start_failed", error=str(e))

    # Check available models
    try:
        from scout.core.model_router import model_router
        await model_router.check_models_available()
        logger.info("models_checked")
    except Exception as e:
        logger.warning("model_check_failed", error=str(e))

    yield

    # --- Shutdown ---
    logger.info("application_shutting_down")
    
    # Stop Supervisor Agent
    try:
        from scout.agents.supervisor import supervisor
        await supervisor.stop()
    except Exception as e:
        logger.error("supervisor_stop_error", error=str(e))

    # Close database connections
    try:
        from scout.infrastructure.database import close_db
        await close_db()
    except Exception as e:
        logger.warning("database_close_error", reason=str(e))


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This factory pattern allows for easy testing and configuration.
    """
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered autonomous cybersecurity agent",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # CORS middleware (development: allow any localhost/127.0.0.1 port)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?$" if settings.environment == "development" else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(ScoutError, scout_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Root: API docs'a yönlendir (localhost:8000 → /docs)
    @app.get("/", include_in_schema=False)
    def _root():
        return RedirectResponse(url="/docs")

    # Include API routers
    app.include_router(api_v1_router, prefix=settings.api_prefix)

    return app


# Application instance
app = create_app()
