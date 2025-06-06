"""
FastAPI Application Entry Point

This module creates and configures the FastAPI application instance.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.database import check_database_connection

# Import routers
from app.routers import web

# Get application settings
settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    
    This function handles startup and shutdown events for the FastAPI application
    
    Startup tasks:
    - Check database connection
    - Initialize any required services
    
    Shutdown tasks:
    - Clean up resources
    - Close connections
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Check database connection
    if check_database_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
        raise Exception("Could not connect to database")

    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown initiated")
    # Add cleanup tasks here if needed
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Application factory function.
    
    Creates and configures the FastAPI application instance.
    This pattern allows for easy testing and multiple configurations.
    
    Returns:
        FastAPI: Configured application instance
    """
    
    # Create FastAPI application
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Configure templates
    templates = Jinja2Templates(directory="templates")
    
    # Add templates to app state for access in routes
    app.state.templates = templates
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Global exception handler for unhandled errors.

        Provides consistent error responses across the application.
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        if settings.debug:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": str(exc),
                    "type": type(exc).__name__
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "detail": "An unexpected error occurred"
                }
            )
    
    # Register routers
    app.include_router(web.router)

    return app


# Create application instance
app = create_app()


def main() -> None:
    """
    Main entry point for running the application.
    
    This function is used when running the application directly
    or through the CLI command defined in pyproject.toml.
    """
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
