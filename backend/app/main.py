"""FastAPI application main module."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.middleware.errors import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
    quote_generation_exception_handler,
    QuoteGenerationError
)
from app.routes import health, quote


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting CPQ Backend API")
    yield
    # Shutdown
    logger.info("Shutting down CPQ Backend API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="CPQ Backend API",
        description="FastAPI backend for CPQ system with AI-powered quote generation",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add exception handlers
    app.add_exception_handler(
        QuoteGenerationError,
        quote_generation_exception_handler
    )
    app.add_exception_handler(
        Exception,
        general_exception_handler
    )
    
    # Include routers
    app.include_router(health.router)
    app.include_router(quote.router)
    
    return app


# Create the app instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CPQ Backend API",
        "version": "0.1.0",
        "docs": "/docs"
    }